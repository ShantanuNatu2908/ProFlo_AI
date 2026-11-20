import os
import pickle
import numpy as np
import torch
import yfinance as yf
from fastapi import APIRouter, HTTPException

from app.ml.trainer import (
    SEQ_LENGTH,
    WEIGHTS_DIR,
    StockLSTM,
    extract_close_prices,
    train_model_on_demand,
)

router = APIRouter(prefix="/predict", tags=["Predict"])


@router.post("/{ticker}")
def run_prediction(ticker: str):
    ticker = ticker.upper().strip()
    model_path = os.path.join(WEIGHTS_DIR, f"{ticker}.pth")
    scaler_path = os.path.join(WEIGHTS_DIR, f"{ticker}_scaler.pkl")

    # 1. Auto-train if weights or scaler do not exist yet
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        try:
            train_model_on_demand(ticker)
        except ValueError as ve:
            raise HTTPException(status_code=404, detail=str(ve))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Auto-training failed for {ticker}: {str(e)}",
            )

    # 2. Load model and scaler (retrain automatically if an older weight format clashes)
    model = StockLSTM(input_size=1, hidden_size=50, num_layers=2, output_size=1)
    try:
        model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu"), weights_only=True))
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)
    except Exception:
        train_model_on_demand(ticker)
        model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu"), weights_only=True))
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)

    model.eval()

    # 3. Fetch recent market data (6 months ensures >= 60 trading days)
    df = yf.download(ticker, period="6mo", progress=False)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"Could not fetch recent data for {ticker}.")

    close_series = extract_close_prices(df)
    if len(close_series) < SEQ_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough recent trading days for {ticker} to run a {SEQ_LENGTH}-day prediction.",
        )

    # 4. Prepare the 3D tensor (1, 60, 1) and run inference
    last_60_prices = close_series.values[-SEQ_LENGTH:].reshape(-1, 1).astype(np.float32)
    scaled_input = scaler.transform(last_60_prices)
    input_tensor = torch.tensor(scaled_input, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        predicted_scaled = model(input_tensor).numpy()

    predicted_next_close = float(scaler.inverse_transform(predicted_scaled)[0][0])
    last_actual_close = float(close_series.values[-1])
    trend = "BULLISH" if predicted_next_close >= last_actual_close else "BEARISH"

    # 5. Format last 30 days for the Recharts line chart
    last_30 = close_series.tail(30)
    historical_data = [
        {"date": idx.strftime("%Y-%m-%d"), "price": round(float(val), 2)}
        for idx, val in last_30.items()
    ]

    return {
        "ticker": ticker,
        "current_price": round(last_actual_close, 2),
        "predicted_next_close": round(predicted_next_close, 2),
        "trend": trend,
        "historical_data": historical_data,
    }