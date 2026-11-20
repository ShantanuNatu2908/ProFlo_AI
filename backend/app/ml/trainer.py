import os
import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler

WEIGHTS_DIR = "app/ml/weights"
SEQ_LENGTH = 60


class StockLSTM(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 50, num_layers: int = 2, output_size: int = 1):
        super(StockLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


def extract_close_prices(df: pd.DataFrame) -> pd.Series:
    """Safely extract 1D Close price series across all yfinance versions."""
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.dropna()


def train_model_on_demand(ticker: str, epochs: int = 15) -> tuple[str, str]:
    """Downloads 2 years of data, trains a 60-day LSTM, and saves weights + scaler."""
    ticker = ticker.upper().strip()
    print(f"[ProfLo AI] Auto-training LSTM model for {ticker}...")

    df = yf.download(ticker, period="2y", progress=False)
    if df is None or df.empty:
        raise ValueError(f"No market data found for ticker '{ticker}' on Yahoo Finance.")

    close_series = extract_close_prices(df)
    if len(close_series) <= SEQ_LENGTH + 1:
        raise ValueError(f"Not enough historical data for '{ticker}' (need > {SEQ_LENGTH} trading days).")

    prices = close_series.values.reshape(-1, 1).astype(np.float32)

    # Scale prices between 0 and 1
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_prices = scaler.fit_transform(prices)

    # Build 60-day sequences to predict day 61
    X, y = [], []
    for i in range(SEQ_LENGTH, len(scaled_prices)):
        X.append(scaled_prices[i - SEQ_LENGTH : i, 0])
        y.append(scaled_prices[i, 0])

    X_tensor = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1)  # (N, 60, 1)
    y_tensor = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(-1)  # (N, 1)

    model = StockLSTM(input_size=1, hidden_size=50, num_layers=2, output_size=1)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_tensor)
        loss = criterion(outputs, y_tensor)
        loss.backward()
        optimizer.step()

    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    model_path = os.path.join(WEIGHTS_DIR, f"{ticker}.pth")
    scaler_path = os.path.join(WEIGHTS_DIR, f"{ticker}_scaler.pkl")

    torch.save(model.state_dict(), model_path)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    print(f"[ProfLo AI] Finished training {ticker}. Saved to {model_path}")
    return model_path, scaler_path