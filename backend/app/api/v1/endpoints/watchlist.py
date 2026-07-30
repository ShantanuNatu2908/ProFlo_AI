from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.v1.endpoints.auth import get_current_user
from app.db.models import User, Watchlist
from app.db.session import get_db

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("/")
def get_watchlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    return {"watchlist": [item.ticker for item in items]}

@router.post("/{ticker}")
def toggle_watchlist(ticker: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticker = ticker.upper()
    # Check if it already exists
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id, 
        Watchlist.ticker == ticker
    ).first()
    
    if existing:
        # If it exists, remove it (Toggle Off)
        db.delete(existing)
        db.commit()
        return {"message": f"Removed {ticker}", "status": "removed"}
    else:
        # If it doesn't exist, add it (Toggle On)
        new_item = Watchlist(user_id=current_user.id, ticker=ticker)
        db.add(new_item)
        db.commit()
        return {"message": f"Added {ticker}", "status": "added"}