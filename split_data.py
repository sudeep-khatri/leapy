import os
import pandas as pd
from sklearn.model_selection import train_test_split
df = pd.read_csv("transcription_clean.csv")
train_df, temp_df = train_test_split(df, test_size=0.20, random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=42)

os.makedirs("data_splits", exist_ok=True)
train_df.to_csv("data_splits/train.csv", index=False)
val_df.to_csv("data_splits/val.csv", index=False)
test_df.to_csv("data_splits/test.csv", index=False)