import os
import argparse
import pandas as pd
from src.inference import PrachalitOCR
from src.utils import resolve_image_path


def run_csv_test(ocr, csv_path, images_dir="images"):
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found.")
        return

    df = pd.read_csv(csv_path)
    img_col = (
        "image_path"
        if "image_path" in df.columns
        else ("image" if "image" in df.columns else df.columns[0])
    )
    text_col = "text" if "text" in df.columns else df.columns[1]

    print(f"\n--- Testing Dataset: {csv_path} ---")
    for idx, row in df.iterrows():
        raw_filename = row[img_col]
        ground_truth = row[text_col] if text_col in df.columns else "N/A"
        img_path = resolve_image_path(images_dir, raw_filename)

        if img_path:
            predicted_text = ocr.predict(img_path)
            print("=" * 55)
            print(f" Image File   : {img_path}")
            print(f" Ground Truth : {ground_truth}")
            print(f" Recognized   : {predicted_text}")
            print("=" * 55 + "\n")
        else:
            print(
                f"Could not locate image '{raw_filename}' in '{images_dir}/'."
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prachalit OCR Predictor")
    parser.add_argument(
        "--image", type=str, help="Path to a single image file"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="data_splits/random.csv",
        help="Path to a CSV file",
    )

    args = parser.parse_args()
    ocr = PrachalitOCR()

    if args.image:
        result = ocr.predict(args.image)
        print(f"\nImage: {args.image}\nOCR Result: {result}\n")
    else:
        run_csv_test(ocr, args.csv)