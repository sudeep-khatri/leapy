import json
import os
import cv2
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

# 1. Load Vocabulary Map
with open("ml/vocabulary.json", "r", encoding="utf-8") as f:
    vocab = json.load(f)

# Reverse vocabulary map (ID -> Character)
char_map = {v: k for k, v in vocab.items()}


# 2. Text Encoder & Decoder Functions
def encode_text(text, vocab_map):
    """Converts a Prachalit text string into a tensor of integer token IDs."""
    encoded = []
    for char in text:
        if char in vocab_map:
            encoded.append(vocab_map[char])
    return torch.tensor(encoded, dtype=torch.long)


def decode_ids(ids, char_map):
    """Converts integer predictions back into Prachalit text."""
    blank_idx = vocab.get("<BLANK>", 78)
    decoded = []
    prev = None
    for i in ids:
        if i != prev and i != blank_idx:
            decoded.append(char_map.get(i, ""))
        prev = i
    return "".join(decoded)


# 3. Custom PyTorch Dataset
class PrachalitOCRDataset(Dataset):

    def __init__(
        self,
        csv_file="ml/transcription_clean.csv",
        img_dir="ml/images",
        vocab_dict=vocab,
        target_h=32,
        target_w=512,
    ):
        self.df = pd.read_csv(csv_file)
        self.img_dir = img_dir
        self.vocab = vocab_dict
        self.target_h = target_h
        self.target_w = target_w

    def __len__(self):
        return len(self.df)

    def _find_image_path(self, raw_name):
        """Helper to find image path across possible extensions (.png, .jpg, .jpeg)."""
        base_path = os.path.join(self.img_dir, str(raw_name))

        # Check direct path first (in case extension is already in CSV)
        if os.path.exists(base_path):
            return base_path

        # Check with common extensions
        for ext in [".jpg", ".png", ".jpeg", ".JPG", ".PNG"]:
            possible_path = f"{base_path}{ext}"
            if os.path.exists(possible_path):
                return possible_path

        raise FileNotFoundError(
            f"Image file '{raw_name}' not found inside '{self.img_dir}/' with .jpg, .png, or .jpeg extensions."
        )

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = self._find_image_path(row["image"])

        # Read Grayscale
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Failed to read image at: {img_path}")

        # Contrast Enhancement (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img)

        # Aspect Ratio Resizing + Padding to (32, 512)
        h, w = enhanced.shape
        scale = self.target_h / float(h)
        new_w = int(w * scale)
        resized = cv2.resize(
            enhanced, (new_w, self.target_h), interpolation=cv2.INTER_AREA
        )

        if new_w < self.target_w:
            padding = (
                np.ones(
                    (self.target_h, self.target_w - new_w), dtype=np.uint8
                )
                * 255
            )
            final_img = np.hstack((resized, padding))
        else:
            final_img = cv2.resize(
                enhanced,
                (self.target_w, self.target_h),
                interpolation=cv2.INTER_AREA,
            )

        # Normalize to [0.0, 1.0] and reshape to (1, 32, 512)
        normalized = final_img.astype(np.float32) / 255.0
        tensor_img = torch.tensor(normalized).unsqueeze(0)

        # Target label tensor
        label_tensor = encode_text(str(row["text"]), self.vocab)

        return tensor_img, label_tensor, str(row["text"])


if __name__ == "__main__":
    dataset = PrachalitOCRDataset()
    print(f"✓ Dataset verified with {len(dataset)} line samples.")