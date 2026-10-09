import torch
import pandas as pd
from model import CRNN
from ocr_dataset import PrachalitOCRDataset, vocab, char_map, decode_ids

def run_evaluation():
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading checkpoint on {DEVICE}...")

    # Load Model
    num_classes = len(vocab) + 1
    model = CRNN(num_classes=num_classes).to(DEVICE)
    model.load_state_dict(torch.load("checkpoints/crnn_epoch_10.pth", map_location=DEVICE))
    model.eval()

    # Load Test Dataset
    test_dataset = PrachalitOCRDataset(csv_file="data_splits/test.csv", img_dir="images")

    print("\n--- SAMPLE PREDICTIONS ON HELD-OUT TEST SET ---")
    with torch.no_grad():
        for i in range(5):  # Sample first 5 test lines
            img_tensor, label_tensor, ground_truth = test_dataset[i]
            img_input = img_tensor.unsqueeze(0).to(DEVICE)

            logits = model(img_input)  # Output shape: (1, 127, 79)
            preds = torch.argmax(logits, dim=2).squeeze(0).cpu().numpy()

            predicted_text = decode_ids(preds, char_map)

            print(f"\n[Sample {i+1}]")
            print(f"Ground Truth : {ground_truth}")
            print(f"Predicted    : {predicted_text}")

if __name__ == "__main__":
    run_evaluation()