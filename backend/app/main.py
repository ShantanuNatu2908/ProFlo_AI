from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine, Base
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import predict, stocks, auth

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ProfLo AI - Market Predictor", version="1.0.0")

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to standard React dev server (e.g. http://localhost:3000) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(stocks.router, prefix="/api/v1")
app.include_router(predict.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"status": "online", "system": "ProfLo AI Core API"}