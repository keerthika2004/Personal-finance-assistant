import pandas as pd
from prophet import Prophet
import logging
import warnings
from typing import List, Dict, Any

# Suppress Prophet logging noise
logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("cmdstanpy").disabled=True
warnings.filterwarnings("ignore")

def generate_forecast(transactions: List[Dict[str, Any]], periods: int = 30) -> Dict[str, List[Any]]:
    """
    Generates a cashflow forecast based on historical transactions.
    Groups amounts by day and predicts the next `periods` days.
    """
    if not transactions or len(transactions) < 10:
        return {"dates": [], "yhat": [], "yhat_lower": [], "yhat_upper": []}
        
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    
    # Aggregate by day
    daily = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
    daily.columns = ['ds', 'y']
    
    try:
        m = Prophet(daily_seasonality=False)
        m.fit(daily)
        
        future = m.make_future_dataframe(periods=periods)
        forecast = m.predict(future)
        
        # Only return the future forecasted period
        future_forecast = forecast.tail(periods)
        
        return {
            "dates": future_forecast['ds'].dt.strftime("%Y-%m-%d").tolist(),
            "yhat": future_forecast['yhat'].round(2).tolist(),
            "yhat_lower": future_forecast['yhat_lower'].round(2).tolist(),
            "yhat_upper": future_forecast['yhat_upper'].round(2).tolist()
        }
    except Exception as e:
        print(f"Forecasting error: {e}")
        return {"dates": [], "yhat": [], "yhat_lower": [], "yhat_upper": []}
