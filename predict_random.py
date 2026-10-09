import os
import cv2
import numpy as np
import pandas as pd
import torch
from model import CRNN
from ocr_dataset import char_map, decode_ids, vocab

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

