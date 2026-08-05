import pandas as pd
import numpy as np
from prophet import Prophet
import sys
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
import warnings

# Suppress Prophet logging noise
import logging
logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("cmdstanpy").disabled=True
warnings.filterwarnings("ignore")

def generate_mock_cashflow_data():
    """Generates 2 years of daily cashflow for backtesting"""
    dates = pd.date_range(start='2022-01-01', end='2023-12-31', freq='D')
    df = pd.DataFrame({'ds': dates})
    
    # Base expenses
    np.random.seed(42)
    base = -100 + np.random.normal(0, 30, len(dates))
    
    # Weekly seasonality (higher expenses on weekends)
    weekly = np.where(df['ds'].dt.dayofweek >= 5, -50, 0)
    
    # Monthly seasonality (rent on 1st)
    monthly = np.where(df['ds'].dt.day == 1, -1500, 0)
    
    # Add income (Salary 15th and 30th)
    income = np.where(df['ds'].dt.day.isin([15, 30]), 2500, 0)
    
    df['y'] = base + weekly + monthly + income
    return df

def run_backtest():
    print("Generating historic cashflow data for backtesting...")
    df = generate_mock_cashflow_data()
    
    # Train-test split (predict last 60 days)
    train = df.iloc[:-60]
    test = df.iloc[-60:]
    
    print("Training Prophet Model...")
    m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
    m.fit(train)
    
    print("Predicting and evaluating (Backtest)...")
    future = m.make_future_dataframe(periods=60)
    forecast = m.predict(future)
    
    pred = forecast.iloc[-60:]['yhat'].values
    actual = test['y'].values
    
    mae = mean_absolute_error(actual, pred)
    # Exclude strict zeros for MAPE to avoid inf
    mask = actual != 0
    mape = mean_absolute_percentage_error(actual[mask], pred[mask])
    
    print(f"Backtest MAE: ${mae:.2f}")
    print(f"Backtest MAPE: {mape*100:.2f}%")
    
    # Save to eval/benchmark.txt
    with open('eval/benchmark.txt', 'a') as f:
        f.write("\n## Cashflow Forecasting (Prophet)\n")
        f.write(f"- **MAE**: ${mae:.2f}\n")
        f.write(f"- **MAPE**: {mape*100:.2f}%\n")
        
    print("Saved to eval/benchmark.txt")

if __name__ == "__main__":
    run_backtest()
