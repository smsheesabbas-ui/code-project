import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from prophet import Prophet
from ..database import transactions
from ..config import settings


class ProphetService:
    def __init__(self):
        self.min_days_required = 60
        self.min_transactions_required = 50
    
    async def generate_cashflow_forecast(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Generate cashflow forecast using Prophet"""
        
        # Check if user has sufficient data
        data_check = await self._check_data_sufficiency(user_id)
        if not data_check["sufficient"]:
            return {
                "status": "insufficient_data",
                "message": data_check["message"],
                "current_data": {
                    "days_of_history": data_check["days_of_history"],
                    "transaction_count": data_check["transaction_count"]
                }
            }
        
        # Get transaction data
        df = await self._get_transaction_data(user_id)
        
        if df.empty:
            return {
                "status": "no_data",
                "message": "No transaction data found"
            }
        
        try:
            # Prepare data for Prophet
            prophet_df = self._prepare_prophet_data(df)
            
            # Fit model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05
            )
            
            model.fit(prophet_df)
            
            # Generate forecast
            future = model.make_future_dataframe(periods=days, include_history=True)
            forecast = model.predict(future)
            
            # Extract relevant forecast data
            forecast_data = self._extract_forecast_data(forecast, days)
            
            # Calculate key metrics
            metrics = self._calculate_forecast_metrics(df, forecast_data)
            
            return {
                "status": "success",
                "forecast": forecast_data,
                "metrics": metrics,
                "model_info": {
                    "training_data_points": len(prophet_df),
                    "forecast_days": days,
                    "data_period": {
                        "start": prophet_df['ds'].min().isoformat(),
                        "end": prophet_df['ds'].max().isoformat()
                    }
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Forecast generation failed: {str(e)}"
            }
    
    async def _check_data_sufficiency(self, user_id: str) -> Dict[str, Any]:
        """Check if user has sufficient data for forecasting"""
        
        # Get date range and transaction count
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "earliest_date": {"$min": "$transaction_date"},
                "latest_date": {"$max": "$transaction_date"},
                "transaction_count": {"$sum": 1}
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if not result or result[0]["transaction_count"] == 0:
            return {
                "sufficient": False,
                "message": "No transaction data available",
                "days_of_history": 0,
                "transaction_count": 0
            }
        
        data = result[0]
        days_of_history = (data["latest_date"] - data["earliest_date"]).days
        
        sufficient = (
            days_of_history >= self.min_days_required and
            data["transaction_count"] >= self.min_transactions_required
        )
        
        message = "Sufficient data for forecasting"
        if not sufficient:
            if days_of_history < self.min_days_required:
                message = f"Need at least {self.min_days_required} days of history (have {days_of_history})"
            else:
                message = f"Need at least {self.min_transactions_required} transactions (have {data['transaction_count']})"
        
        return {
            "sufficient": sufficient,
            "message": message,
            "days_of_history": days_of_history,
            "transaction_count": data["transaction_count"]
        }
    
    async def _get_transaction_data(self, user_id: str) -> pd.DataFrame:
        """Get transaction data as pandas DataFrame"""
        
        cursor = transactions.find(
            {"user_id": user_id},
            {"transaction_date": 1, "amount": 1}
        ).sort("transaction_date", 1)
        
        data = []
        async for doc in cursor:
            data.append({
                "date": doc["transaction_date"],
                "amount": float(doc["amount"])
            })
        
        return pd.DataFrame(data)
    
    def _prepare_prophet_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for Prophet model"""
        
        # Group by date and sum amounts
        daily_data = df.groupby('date')['amount'].sum().reset_index()
        daily_data.columns = ['ds', 'y']
        
        # Ensure no gaps in dates
        min_date = daily_data['ds'].min()
        max_date = daily_data['ds'].max()
        all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
        
        # Fill missing dates with 0
        complete_df = pd.DataFrame({'ds': all_dates})
        complete_df = complete_df.merge(daily_data, on='ds', how='left')
        complete_df['y'] = complete_df['y'].fillna(0)
        
        return complete_df
    
    def _extract_forecast_data(self, forecast: pd.DataFrame, days: int) -> List[Dict[str, Any]]:
        """Extract forecast data for the specified number of days"""
        
        # Get only future predictions
        future_forecast = forecast.tail(days)
        
        forecast_data = []
        for _, row in future_forecast.iterrows():
            forecast_data.append({
                "date": row['ds'].isoformat(),
                "predicted_amount": float(row['yhat']),
                "lower_bound": float(row['yhat_lower']),
                "upper_bound": float(row['yhat_upper']),
                "trend": float(row['trend'])
            })
        
        return forecast_data
    
    def _calculate_forecast_metrics(self, historical_data: pd.DataFrame, forecast_data: List[Dict]) -> Dict[str, Any]:
        """Calculate key metrics from forecast"""
        
        # Historical metrics
        historical_avg = historical_data.groupby('date')['amount'].sum().mean()
        historical_std = historical_data.groupby('date')['amount'].sum().std()
        
        # Forecast metrics
        forecast_amounts = [f["predicted_amount"] for f in forecast_data]
        forecast_avg = sum(forecast_amounts) / len(forecast_amounts)
        
        # Projected ending balance
        current_balance = await self._get_current_balance(historical_data)
        projected_balance = current_balance + sum(forecast_amounts)
        
        # Cashflow risk assessment
        min_forecast = min(f["lower_bound"] for f in forecast_data)
        cashflow_risk = "high" if min_forecast < -1000 else "medium" if min_forecast < 0 else "low"
        
        return {
            "historical_daily_average": float(historical_avg),
            "historical_volatility": float(historical_std) if not pd.isna(historical_std) else 0.0,
            "forecast_daily_average": float(forecast_avg),
            "projected_balance": float(projected_balance),
            "cashflow_risk": cashflow_risk,
            "trend_direction": "increasing" if forecast_avg > historical_avg else "decreasing"
        }
    
    async def _get_current_balance(self, historical_data: pd.DataFrame) -> float:
        """Calculate current running balance"""
        # This is a simplified calculation
        # In production, you'd maintain a running balance field
        return float(historical_data['amount'].sum())


prophet_service = ProphetService()
