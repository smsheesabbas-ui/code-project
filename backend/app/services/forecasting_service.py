import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from prophet import Prophet
from app.core.database import get_database


class ForecastingService:
    """Cashflow forecasting using Facebook Prophet"""
    
    def __init__(self):
        self.min_days_required = 60
        self.min_transactions_required = 50
    
    async def generate_forecast(self, user_id: str, days: int = 30) -> Optional[Dict]:
        """Generate cashflow forecast for user"""
        try:
            # Get user's transaction history
            transactions = await self._get_transaction_data(user_id)
            
            # Check if we have sufficient data
            if not self._has_sufficient_data(transactions):
                return {
                    "status": "insufficient_data",
                    "message": f"Need at least {self.min_days_required} days and {self.min_transactions_required} transactions",
                    "current_days": self._get_data_range_days(transactions),
                    "current_transactions": len(transactions)
                }
            
            # Prepare data for Prophet
            df = self._prepare_prophet_data(transactions)
            
            # Create and fit Prophet model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,  # Will be disabled if insufficient data
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0
            )
            
            model.fit(df)
            
            # Make future dataframe
            future = model.make_future_dataframe(periods=days, include_history=False)
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Prepare results
            results = self._format_forecast_results(forecast, days)
            
            # Calculate confidence metrics
            confidence_metrics = self._calculate_confidence_metrics(df, forecast)
            
            return {
                "status": "success",
                "forecast": results,
                "confidence_metrics": confidence_metrics,
                "data_points": len(transactions),
                "forecast_period_days": days,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating forecast: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _get_transaction_data(self, user_id: str) -> List[Dict]:
        """Get transaction data for user"""
        db = get_database()
        
        transactions = await db.transactions.find({
            "user_id": user_id,
            "transaction_date": {"$gte": datetime.utcnow() - timedelta(days=365)}
        }).sort("transaction_date", 1).to_list(length=None)
        
        return transactions
    
    def _has_sufficient_data(self, transactions: List[Dict]) -> bool:
        """Check if we have sufficient data for forecasting"""
        if len(transactions) < self.min_transactions_required:
            return False
        
        data_range_days = self._get_data_range_days(transactions)
        return data_range_days >= self.min_days_required
    
    def _get_data_range_days(self, transactions: List[Dict]) -> int:
        """Get the range of data in days"""
        if not transactions:
            return 0
        
        first_date = transactions[0]["transaction_date"]
        last_date = transactions[-1]["transaction_date"]
        
        if isinstance(first_date, str):
            first_date = datetime.fromisoformat(first_date.replace('Z', '+00:00'))
        elif hasattr(first_date, 'date'):
            first_date = first_date.date()
        if isinstance(last_date, str):
            last_date = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
        elif hasattr(last_date, 'date'):
            last_date = last_date.date()
        
        if hasattr(first_date, 'day') and hasattr(last_date, 'day'):
            return (last_date - first_date).days
        return 0
    
    def _prepare_prophet_data(self, transactions: List[Dict]) -> pd.DataFrame:
        """Prepare transaction data for Prophet"""
        # Aggregate transactions by date
        daily_data = {}
        
        for transaction in transactions:
            date = transaction["transaction_date"]
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
            elif isinstance(date, datetime):
                date = date.date()
            
            if date not in daily_data:
                daily_data[date] = 0.0
            
            daily_data[date] += float(transaction["amount"])
        
        # Create DataFrame
        df_data = []
        for date, amount in sorted(daily_data.items()):
            df_data.append({
                "ds": date,
                "y": amount
            })
        
        df = pd.DataFrame(df_data)
        
        # Fill missing dates with 0 (no transactions)
        date_range = pd.date_range(
            start=df["ds"].min(),
            end=df["ds"].max(),
            freq="D"
        )
        
        df = df.set_index("ds").reindex(date_range, fill_value=0).reset_index()
        df.rename(columns={"index": "ds"}, inplace=True)
        
        return df
    
    def _format_forecast_results(self, forecast: pd.DataFrame, days: int) -> Dict:
        """Format forecast results"""
        # Get the last 'days' predictions
        recent_forecast = forecast.tail(days)
        
        # Calculate daily, weekly, and monthly summaries
        daily_forecast = []
        for _, row in recent_forecast.iterrows():
            daily_forecast.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "predicted_amount": round(float(row["yhat"]), 2),
                "lower_bound": round(float(row["yhat_lower"]), 2),
                "upper_bound": round(float(row["yhat_upper"]), 2)
            })
        
        # Calculate weekly aggregates
        weekly_forecast = self._aggregate_forecast_by_period(recent_forecast, "W")
        
        # Calculate monthly aggregates
        monthly_forecast = self._aggregate_forecast_by_period(recent_forecast, "M")
        
        # Calculate summary statistics
        total_predicted = recent_forecast["yhat"].sum()
        avg_daily = recent_forecast["yhat"].mean()
        min_predicted = recent_forecast["yhat"].min()
        max_predicted = recent_forecast["yhat"].max()
        
        return {
            "daily": daily_forecast,
            "weekly": weekly_forecast,
            "monthly": monthly_forecast,
            "summary": {
                "total_predicted": round(float(total_predicted), 2),
                "average_daily": round(float(avg_daily), 2),
                "minimum_daily": round(float(min_predicted), 2),
                "maximum_daily": round(float(max_predicted), 2),
                "trend_direction": "upward" if avg_daily > 0 else "downward" if avg_daily < 0 else "stable"
            }
        }
    
    def _aggregate_forecast_by_period(self, forecast: pd.DataFrame, period: str) -> List[Dict]:
        """Aggregate forecast by period (weekly or monthly)"""
        forecast_copy = forecast.copy()
        forecast_copy["period"] = forecast_copy["ds"].dt.to_period(period)
        
        aggregated = forecast_copy.groupby("period").agg({
            "yhat": "sum",
            "yhat_lower": "sum",
            "yhat_upper": "sum"
        }).reset_index()
        
        result = []
        for _, row in aggregated.iterrows():
            period_start = row["period"].start_time
            result.append({
                "period_start": period_start.strftime("%Y-%m-%d"),
                "period_end": row["period"].end_time.strftime("%Y-%m-%d"),
                "predicted_amount": round(float(row["yhat"]), 2),
                "lower_bound": round(float(row["yhat_lower"]), 2),
                "upper_bound": round(float(row["yhat_upper"]), 2)
            })
        
        return result
    
    def _calculate_confidence_metrics(self, historical_data: pd.DataFrame, forecast: pd.DataFrame) -> Dict:
        """Calculate confidence metrics for the forecast"""
        # Simple confidence based on data quality and consistency
        data_points = len(historical_data)
        data_range_days = (historical_data["ds"].max() - historical_data["ds"].min()).days
        
        # Base confidence from data volume
        volume_confidence = min(data_points / 100, 1.0)  # Max confidence at 100+ data points
        
        # Confidence from data consistency (lower variance = higher confidence)
        variance = historical_data["y"].var()
        mean_amount = historical_data["y"].mean()
        coefficient_of_variation = variance / (mean_amount ** 2) if mean_amount != 0 else 1
        
        consistency_confidence = max(0, 1 - coefficient_of_variation)
        
        # Confidence from data range
        range_confidence = min(data_range_days / 365, 1.0)  # Max confidence at 1+ year
        
        # Overall confidence (weighted average)
        overall_confidence = (
            volume_confidence * 0.4 +
            consistency_confidence * 0.4 +
            range_confidence * 0.2
        )
        
        return {
            "overall_confidence": round(overall_confidence, 3),
            "volume_confidence": round(volume_confidence, 3),
            "consistency_confidence": round(consistency_confidence, 3),
            "range_confidence": round(range_confidence, 3),
            "data_points": data_points,
            "data_range_days": data_range_days,
            "variance": round(variance, 2),
            "mean_amount": round(mean_amount, 2)
        }


# Global instance
forecasting_service = ForecastingService()
