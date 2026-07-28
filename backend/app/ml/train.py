import os
import torch
import torch.nn as nn
import torch.optim as optim
import yfinance as yf

# Import our custom model and utilities
from app.ml.model import StockPredictorLSTM
from app.ml.utils import scale_data, create_sequences

def train_model(ticker="RELIANCE.NS", epochs=100, learning_rate=0.005, seq_length=60):
    print(f"Fetching 5-year historical data for {ticker}...")
    
    # 1. Fetch Data
    stock = yf.Ticker(ticker)
    hist = stock.history(period="5y")
    
    if hist.empty:
        print(f"Error: No data found for {ticker}.")
        return

    # Extract just the 'Close' prices for this basic model
    data = hist['Close'].values

    # 2. Preprocess Data
    print("Scaling and sequencing data...")
    scaled_data, scaler = scale_data(data)
    X, y = create_sequences(scaled_data, seq_length=seq_length)

    # PyTorch LSTMs expect input shape: (batch_size, sequence_length, features)
    # We add a dimension for the single 'Close' price feature
    #X = X.unsqueeze(-1)

    # Split into training and testing sets (80% train, 20% test)
    train_size = int(len(X) * 0.8)
    X_train, y_train = X[:train_size], y[:train_size]

    # 3. Initialize Model, Loss Function, and Optimizer
    print("Initializing PyTorch LSTM model...")
    model = StockPredictorLSTM(input_size=1, hidden_size=50, num_layers=2, output_size=1)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # 4. Training Loop
    print(f"Starting training for {epochs} epochs...")
    for epoch in range(epochs):
        model.train()         # Set model to training mode
        optimizer.zero_grad() # Clear old gradients

        # Forward pass: predict the prices
        outputs = model(X_train)
        
        # Calculate the loss (how wrong the model was)
        # Squeeze outputs to match the shape of y_train
        loss = criterion(outputs.squeeze(), y_train)

        # Backward pass: compute gradients
        loss.backward()
        
        # Optimize: update the weights
        optimizer.step()

        # Print progress every 10 epochs
        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch + 1}/{epochs}], Loss: {loss.item():.6f}')

    # 5. Save the Trained Model Weights
    weights_dir = "app/ml/weights"
    os.makedirs(weights_dir, exist_ok=True)
    
    save_path = f"{weights_dir}/{ticker}_lstm.pth"
    torch.save(model.state_dict(), save_path)
    
    print(f"\nSuccess! Training complete. Model weights saved to: {save_path}")

if __name__ == "__main__":
    # You can change the ticker here to train on any stock you want
    train_model(ticker="RELIANCE.NS", epochs=100)