import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import torch

def scale_data(data: np.ndarray):
    """Scales data to a range between 0 and 1."""
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data.reshape(-1, 1))
    return scaled_data, scaler

def create_sequences(data: np.ndarray, seq_length: int = 60):
    """
    Chops data into sequences. 
    If seq_length is 60, it uses 60 days of data to predict the 61st day.
    """
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        x = data[i:(i + seq_length)]
        y = data[i + seq_length]
        xs.append(x)
        ys.append(y)
        
    # Convert to PyTorch tensors
    return torch.tensor(np.array(xs), dtype=torch.float32), torch.tensor(np.array(ys), dtype=torch.float32)