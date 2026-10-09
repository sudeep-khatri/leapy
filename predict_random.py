import os
import cv2
import numpy as np
import pandas as pd
import torch
from model import CRNN
from ocr_dataset import char_map, decode_ids, vocab

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def resolve_image_path(base_dir, file_name):
    """Finds image file matching extension (.png, .jpg, .jpeg) inside base_dir."""
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
        return None

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: Unable to load image at '{image_path}'.")
        return None
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(img)

    h, w = enhanced.shape
    scale = 32.0 / float(h)
    new_w = max(1, int(w * scale))
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
        torch.load("checkpoints/crnn_best.pth", map_location=DEVICE)
    )
    model.eval()

    with torch.no_grad():
        logits = model(tensor_img)
        preds = torch.argmax(logits, dim=2).squeeze(0).cpu().numpy()
        decoded_text = decode_ids(preds, char_map)

    return decoded_text


def test_random_csv(csv_path="data_splits/random.csv"):
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found.")
        return

    df = pd.read_csv(csv_path)


    img_col = "image" if "image" in df.columns else df.columns[0]
    text_col = "text" if "text" in df.columns else df.columns[1]

    print("\n--- Running Custom Image Prediction ---")
    for idx, row in df.iterrows():
        raw_filename = row[img_col]
        ground_truth = row[text_col] if text_col in df.columns else "N/A"

        image_path = resolve_image_path("images", raw_filename)

        if image_path:
            predicted_prachalit = predict_single_image(image_path)

            print("=" * 55)
            print(f" Image File      : {image_path}")
            print(f" Ground Truth    : {ground_truth}")
            print(f" Transcribed OCR : {predicted_prachalit}")
            print("=" * 55 + "\n")
        else:
            print(
                f"Error: Could not locate image '{raw_filename}' inside 'images/' folder."
            )


if __name__ == "__main__":
    test_random_csv("data_splits/random.csv")