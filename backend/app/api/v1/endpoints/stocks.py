from fastapi import APIRouter, HTTPException, Depends
import yfinance as yf
import pandas as pd
from app.api.v1.endpoints.auth import get_current_user
from app.db.models import User

router = APIRouter(prefix="/stocks", tags=["Market Data"])

@router.get("/history/{ticker}")
def get_stock_history(ticker: str, period: str = "1y", current_user: User = Depends(get_current_user)):
    """
    Fetch historical market data for a given ticker (e.g., AAPL or RELIANCE.NS).
    Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch historical data
        hist = stock.history(period=period)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail="Ticker not found or no data available")

        # Clean up the pandas dataframe for JSON serialization
        hist = hist.reset_index()
        hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')
        
        # We primarily care about the 'Close' price for basic predictions
        data = hist[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_dict(orient="records")
        
        return {
            "ticker": ticker.upper(),
            "period": period,
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")