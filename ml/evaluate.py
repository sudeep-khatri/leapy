import torch
from torch.utils.data import DataLoader
import pandas as pd
from model import CRNN
from ocr_dataset import PrachalitOCRDataset, vocab, char_map, decode_ids
import jiwer

def crnn_collate_fn(batch):
    images = torch.stack([item[0] for item in batch], dim=0)
    targets = [item[1] for item in batch]
    raw_texts = [item[2] for item in batch]
    return images, targets, raw_texts

def evaluate_model():
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Evaluating using device: {DEVICE}")

    test_dataset = PrachalitOCRDataset(csv_file="data_splits/test.csv", img_dir="images")
    test_loader = DataLoader(
        test_dataset, 
        batch_size=16, 
        shuffle=False, 
        collate_fn=crnn_collate_fn
    )

    num_classes = len(vocab) + 1
    model = CRNN(num_classes=num_classes).to(DEVICE)
    model.load_state_dict(torch.load("checkpoints/crnn_best.pth", map_location=DEVICE))
    model.eval()

    ground_truths = []
    predictions = []

    print("\n--- Running Evaluation on Test Set ---")
    with torch.no_grad():
        for images, _, raw_texts in test_loader:
            images = images.to(DEVICE)
            logits = model(images)
            
            preds = torch.argmax(logits, dim=2).cpu().numpy()
            
            for i in range(len(preds)):
                decoded_text = decode_ids(preds[i], char_map)
                predictions.append(decoded_text)
                ground_truths.append(raw_texts[i])

    cer = jiwer.cer(ground_truths, predictions)
    accuracy = (1.0 - cer) * 100

    print(f"\n==========================================")
    print(f"  Test Set Character Error Rate (CER): {cer:.4f}")
    print(f"  Character Recognition Accuracy    : {accuracy:.2f}%")
    print(f"==========================================")

    print("\n--- Sample Predictions ---")
    for i in range(min(5, len(ground_truths))):
        print(f"Sample {i+1}:")
        print(f"  Target    : {ground_truths[i]}")
        print(f"  Predicted : {predictions[i]}")
        print("-" * 40)

if __name__ == "__main__":
    evaluate_model()