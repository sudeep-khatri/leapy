import torch
import torch.nn as nn


class ResBlock(nn.Module):

    def __init__(self, channels):
        super(ResBlock, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(
                channels, channels, kernel_size=3, stride=1, padding=1
            ),
            nn.BatchNorm2d(channels),
            nn.ReLU(True),
            nn.Conv2d(
                channels, channels, kernel_size=3, stride=1, padding=1
            ),
            nn.BatchNorm2d(channels),
        )
        self.relu = nn.ReLU(True)

    def forward(self, x):
        return self.relu(x + self.conv(x))


class CRNN(nn.Module):

    def __init__(self, num_classes=79): 
        super(CRNN, self).__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            nn.MaxPool2d((2, 2), (2, 2)),
            ResBlock(64),
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
            nn.MaxPool2d((2, 2), (2, 2)),
            ResBlock(128),
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            nn.MaxPool2d((2, 1), (2, 1)),
            ResBlock(256),
            nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
            nn.MaxPool2d((2, 1), (2, 1)),
            nn.Conv2d(512, 512, kernel_size=(2, 1), stride=1, padding=0),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
        )

        self.map_to_seq = nn.Linear(512, 256)
        self.rnn = nn.LSTM(
            input_size=256,
            hidden_size=256,
            num_layers=2,
            bidirectional=True,
            batch_first=True,
            dropout=0.2,
        )

        self.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        features = self.cnn(x) 
        features = features.squeeze(2).permute(
            0, 2, 1
        ) 
        seq = self.map_to_seq(features)
        rnn_out, _ = self.rnn(seq)
        logits = self.fc(rnn_out)
        return logits