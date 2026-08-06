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
    
    # Aggregate by day and calculate cumulative balance
    daily_sum = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
    daily_sum['y'] = daily_sum['amount'].cumsum()
    daily = daily_sum[['date', 'y']].rename(columns={'date': 'ds'})
    
    try:
        # Disable seasonality to prevent overfitting on sparse data
        m = Prophet(
            daily_seasonality=False,
            weekly_seasonality=False,
            yearly_seasonality=False
        )
        m.fit(daily)
        
        future = m.make_future_dataframe(periods=periods)
        forecast = m.predict(future)
        
        # Post-hoc anchor adjustment: Shift the entire forecast so it starts precisely at the user's current actual balance.
        # This fixes a known Prophet issue where robust trend lines ignore massive recent jumps (like a Salary deposit)
        actual_last_value = daily['y'].iloc[-1]
        predicted_last_value = forecast.loc[forecast['ds'] == pd.to_datetime(daily['ds'].iloc[-1]), 'yhat'].values[0]
        adjustment = actual_last_value - predicted_last_value
        
        forecast['yhat'] = forecast['yhat'] + adjustment
        forecast['yhat_lower'] = forecast['yhat_lower'] + adjustment
        forecast['yhat_upper'] = forecast['yhat_upper'] + adjustment
        
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
