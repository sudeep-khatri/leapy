import os
import torch
import torch.nn as nn
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader

from model import CRNN
from ocr_dataset import PrachalitOCRDataset, vocab


def crnn_collate_fn(batch):
    images = torch.stack([item[0] for item in batch], dim=0)
    targets = [item[1] for item in batch]
    raw_texts = [item[2] for item in batch]
    return images, targets, raw_texts


def train_ocr():
    BATCH_SIZE = 32
    LEARNING_RATE = 5e-4 
    NUM_EPOCHS = 35
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"Using device: {DEVICE}")

    train_dataset = PrachalitOCRDataset(
        csv_file="data_splits/train.csv", img_dir="images"
    )
    val_dataset = PrachalitOCRDataset(
        csv_file="data_splits/val.csv", img_dir="images"
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        collate_fn=crnn_collate_fn,
        num_workers=2,
        pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        collate_fn=crnn_collate_fn,
        num_workers=2,
        pin_memory=True,
    )

    num_classes = len(vocab)
    model = CRNN(num_classes=num_classes).to(DEVICE)

    criterion = nn.CTCLoss(blank=vocab["<BLANK>"], zero_infinity=True)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4
    )
    scheduler = CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS, eta_min=1e-5)
    scaler = torch.amp.GradScaler("cuda")

    os.makedirs("checkpoints", exist_ok=True)
    best_val_loss = float("inf")

    print("\n--- Starting Deep ResNet-CRNN Training ---")
    for epoch in range(NUM_EPOCHS):
        model.train()
        train_loss = 0.0

        for batch_idx, (images, targets, _) in enumerate(train_loader):
            images = images.to(DEVICE)

            optimizer.zero_grad()

            with torch.amp.autocast("cuda"):
                logits = model(images)
                log_probs = logits.permute(1, 0, 2).log_softmax(2)

                batch_size = images.size(0)
                input_lengths = torch.full(
                    size=(batch_size,),
                    fill_value=logits.size(1),
                    dtype=torch.long,
                )
                target_lengths = torch.tensor(
                    [len(t) for t in targets], dtype=torch.long
                )
                targets_flat = torch.cat(
                    [t for t in targets if len(t) > 0]
                ).to(DEVICE)

                loss = criterion(
                    log_probs, targets_flat, input_lengths, target_lengths
                )

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            scaler.step(optimizer)
            scaler.update()

            train_loss += loss.item()

        scheduler.step()

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for images, targets, _ in val_loader:
                images = images.to(DEVICE)
                with torch.amp.autocast("cuda"):
                    logits = model(images)
                    log_probs = logits.permute(1, 0, 2).log_softmax(2)

                    batch_size = images.size(0)
                    input_lengths = torch.full(
                        size=(batch_size,),
                        fill_value=logits.size(1),
                        dtype=torch.long,
                    )
                    target_lengths = torch.tensor(
                        [len(t) for t in targets], dtype=torch.long
                    )
                    targets_flat = torch.cat(
                        [t for t in targets if len(t) > 0]
                    ).to(DEVICE)

                    loss = criterion(
                        log_probs, targets_flat, input_lengths, target_lengths
                    )
                val_loss += loss.item()

        avg_train = train_loss / len(train_loader)
        avg_val = val_loss / len(val_loader)

        print(
            f"Epoch [{epoch+1:02d}/{NUM_EPOCHS}] | Train Loss: {avg_train:.4f} | Val Loss: {avg_val:.4f}"
        )

        if avg_val < best_val_loss:
            best_val_loss = avg_val
            torch.save(model.state_dict(), "checkpoints/crnn_best.pth")
            print(f"  --> Saved new best checkpoint (Val Loss: {avg_val:.4f})")


if __name__ == "__main__":
    train_ocr()