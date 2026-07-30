import os
import torch
import yfinance as yf
from fastapi import APIRouter, HTTPException, Depends
import numpy as np
import pandas as pd

# Import our ML tools and Auth dependency
from app.ml.model import StockPredictorLSTM
from app.ml.utils import scale_data
from app.api.v1.endpoints.auth import get_current_user
from app.db.models import User

router = APIRouter(prefix="/predict", tags=["AI Predictions"])

@router.post("/{ticker}")
def predict_stock_price(ticker: str, current_user: User = Depends(get_current_user)):
    """
    Generate a next-day stock price prediction using the trained PyTorch LSTM model.
    """
    weights_path = f"app/ml/weights/{ticker}_lstm.pth"
    
    # 1. Check if we have a trained model for this ticker
    if not os.path.exists(weights_path):
        raise HTTPException(
            status_code=404, 
            detail=f"No trained AI model found for {ticker}. Please run the training pipeline first."
        )

    try:
        # 2. Fetch the most recent data (We fetch 1 year to properly fit the scaler)
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        if len(hist) < 60:
            raise HTTPException(status_code=400, detail="Not enough historical data to generate a sequence.")

        data = hist['Close'].values

        # --- NEW: Extract the last 30 days for the React Chart ---
        chart_data_df = hist.tail(30)
        historical_data = []
        for index, row in chart_data_df.iterrows():
            historical_data.append({
                "date": index.strftime("%Y-%m-%d"), 
                "price": float(row["Close"])
            })
        # ---------------------------------------------------------

        # 3. Preprocess the data using the exact same scaling logic as training
        scaled_data, scaler = scale_data(data)
        
        # Grab only the last 60 days to form our prediction sequence
        last_60_days = scaled_data[-60:]
        
        # Shape the tensor to exactly what the LSTM expects: (batch_size=1, sequence_length=60, features=1)
        X_test = torch.tensor(last_60_days, dtype=torch.float32).unsqueeze(0)

        # 4. Load the Model
        model = StockPredictorLSTM(input_size=1, hidden_size=50, num_layers=2, output_size=1)
        model.load_state_dict(torch.load(weights_path))
        model.eval() # Set model to evaluation mode (turns off dropout layers)

        # 5. Generate the Prediction
        with torch.no_grad(): # Disable gradient tracking to save memory/compute
            predicted_scaled_price = model(X_test)
            
        # 6. Inverse transform the prediction back to a real-world currency value
        predicted_price = scaler.inverse_transform(predicted_scaled_price.numpy())

        return {
            "ticker": ticker.upper(),
            "latest_actual_close": round(float(data[-1]), 2),
            "predicted_next_close": round(float(predicted_price[0][0]), 2),
            "trend": "BULLISH" if predicted_price[0][0] > data[-1] else "BEARISH",
            "historical_data": historical_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction engine error: {str(e)}")