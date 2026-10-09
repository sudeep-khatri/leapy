import os
import cv2
import numpy as np
import pandas as pd
import torch
from model import CRNN
from ocr_dataset import char_map, decode_ids, vocab

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_image_path(base_dir, file_name):
    """Finds image file matching extension (.png, .jpg, .jpeg) if missing."""
    full_path = os.path.join(base_dir, str(file_name))
    if os.path.exists(full_path):
        return full_path

    for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG"]:
        if os.path.exists(full_path + ext):
            return full_path + ext

    return None


def predict_single_image(image_path):
    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' not found.")
        return

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: Unable to load image at '{image_path}'.")
        return

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(img)

    h, w = enhanced.shape
    scale = 32.0 / float(h)
    new_w = int(w * scale)
    resized = cv2.resize(enhanced, (new_w, 32), interpolation=cv2.INTER_AREA)

    if new_w < 512:
        padding = np.ones((32, 512 - new_w), dtype=np.uint8) * 255
        final_img = np.hstack((resized, padding))
    else:
        final_img = cv2.resize(
            enhanced, (512, 32), interpolation=cv2.INTER_AREA
        )

    tensor_img = (
        torch.tensor(final_img.astype(np.float32) / 255.0)
        .unsqueeze(0)
        .unsqueeze(0)
        .to(DEVICE)
    )

    num_classes = len(vocab) + 1
    model = CRNN(num_classes=num_classes).to(DEVICE)
    model.load_state_dict(
        torch.load(
            os.path.join(PROJECT_ROOT, "checkpoints", "crnn_best.pth"),
            map_location=DEVICE,
        )
    )
    model.eval()

    with torch.no_grad():
        logits = model(tensor_img)
        preds = torch.argmax(logits, dim=2).squeeze(0).cpu().numpy()
        decoded_text = decode_ids(preds, char_map)

    return decoded_text


if __name__ == "__main__":
    test_csv = os.path.join(PROJECT_ROOT, "data_splits", "test.csv")
    if os.path.exists(test_csv):
        df = pd.read_csv(test_csv)
        row = df.iloc[0]

        img_col = "image_path" if "image_path" in df.columns else df.columns[0]
        text_col = "text" if "text" in df.columns else df.columns[1]

        raw_filename = row[img_col]
        ground_truth = row[text_col] if text_col in df.columns else "N/A"

        image_path = resolve_image_path(
            os.path.join(PROJECT_ROOT, "images"), raw_filename
        )

        if image_path:
            predicted_text = predict_single_image(image_path)
            print("\n" + "=" * 45)
            print(f" Image Path : {image_path}")
            print(f" Ground Truth : {ground_truth}")
            print(f" Transcribed  : {predicted_text}")
            print("=" * 45 + "\n")
        else:
            print(f"Could not locate image '{raw_filename}' inside 'images/'.")
    else:
        print(f"Test CSV not found: {test_csv}")