from datetime import datetime, timedelta
from typing import Dict, Any, List
from ..database import transactions, users
from ..forecasting.prophet_service import prophet_service
from ..insights.service import insights_service
import pandas as pd


class AdvancedDashboardService:
    def __init__(self):
        pass
    
    async def get_trends_data(self, user_id: str, period: str = "90days") -> Dict[str, Any]:
        """Get trends data for dashboard charts"""
        
        # Calculate date range
        if period == "30days":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == "90days":
            start_date = datetime.utcnow() - timedelta(days=90)
        elif period == "1year":
            start_date = datetime.utcnow() - timedelta(days=365)
        else:
            start_date = datetime.utcnow() - timedelta(days=90)
        
        # Get daily revenue and expenses
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": {"$dateTrunc": {"date": "$transaction_date", "unit": "day"}},
                "revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                "expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "net": {"$sum": "$amount"},
                "transactions": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
            {"$project": {
                "date": "$_id",
                "revenue": {"$round": ["$revenue", 2]},
                "expenses": {"$round": ["$expenses", 2]},
                "net": {"$round": ["$net", 2]},
                "transactions": "$transactions"
            }}
        ]
        
        daily_data = await transactions.aggregate(pipeline).to_list(length=None)
        
        # Get weekly aggregates for trend analysis
        weekly_pipeline = [
            {"$match": {
                "user_id": user_id,
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": {"$dateTrunc": {"date": "$transaction_date", "unit": "week"}},
                "revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                "expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "net": {"$sum": "$amount"},
                "transactions": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
            {"$project": {
                "week": "$_id",
                "revenue": {"$round": ["$revenue", 2]},
                "expenses": {"$round": ["$expenses", 2]},
                "net": {"$round": ["$net", 2]},
                "transactions": "$transactions"
            }}
        ]
        
        weekly_data = await transactions.aggregate(weekly_pipeline).to_list(length=None)
        
        # Calculate trend metrics
        trend_metrics = self._calculate_trend_metrics(weekly_data)
        
        return {
            "period": period,
            "daily_data": daily_data,
            "weekly_data": weekly_data,
            "trend_metrics": trend_metrics,
            "data_points": len(daily_data)
        }
    
    async def get_cashflow_timeline(self, user_id: str, days: int = 90) -> Dict[str, Any]:
        """Get cashflow timeline with historical and projected data"""
        
        # Get historical data
        start_date = datetime.utcnow() - timedelta(days=days)
        historical_pipeline = [
            {"$match": {
                "user_id": user_id,
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": {"$dateTrunc": {"date": "$transaction_date", "unit": "day"}},
                "revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                "expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "net": {"$sum": "$amount"},
                "balance": {"$sum": "$amount"}
            }},
            {"$sort": {"_id": 1}},
            {"$project": {
                "date": "$_id",
                "revenue": {"$round": ["$revenue", 2]},
                "expenses": {"$round": ["$expenses", 2]},
                "net": {"$round": ["$net", 2]},
                "type": "historical"
            }}
        ]
        
        historical_data = await transactions.aggregate(historical_pipeline).to_list(length=None)
        
        # Get forecast data
        forecast_result = await prophet_service.generate_cashflow_forecast(user_id, 30)
        
        forecast_data = []
        if forecast_result.get("status") == "success":
            forecast_data = [
                {
                    "date": f["date"],
                    "revenue": max(0, f["predicted_amount"]),
                    "expenses": max(0, -f["predicted_amount"]) if f["predicted_amount"] < 0 else 0,
                    "net": f["predicted_amount"],
                    "lower_bound": f["lower_bound"],
                    "upper_bound": f["upper_bound"],
                    "type": "forecast"
                }
                for f in forecast_result["forecast"]
            ]
        
        # Combine historical and forecast data
        timeline_data = historical_data + forecast_data
        
        # Calculate running balance
        running_balance = 0
        for i, point in enumerate(timeline_data):
            if point["type"] == "historical":
                running_balance += point["net"]
            point["balance"] = running_balance
        
        return {
            "historical_days": days,
            "forecast_days": 30,
            "timeline": timeline_data,
            "forecast_status": forecast_result.get("status"),
            "forecast_metrics": forecast_result.get("metrics", {}),
            "current_balance": running_balance
        }
    
    async def get_anomalies(self, user_id: str, period: str = "90days") -> List[Dict[str, Any]]:
        """Get recent anomalies in financial data"""
        
        # Calculate date range
        if period == "30days":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == "90days":
            start_date = datetime.utcnow() - timedelta(days=90)
        else:
            start_date = datetime.utcnow() - timedelta(days=90)
        
        # Get daily data for anomaly detection
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": {"$dateTrunc": {"date": "$transaction_date", "unit": "day"}},
                "total_amount": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                "expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "transactions": {"$push": {"amount": "$amount", "description": "$description"}}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        daily_data = await transactions.aggregate(pipeline).to_list(length=None)
        
        if len(daily_data) < 7:
            return []  # Not enough data for anomaly detection
        
        # Detect anomalies using Z-score method
        anomalies = []
        
        # Revenue anomalies
        revenue_values = [d.get("revenue", 0) for d in daily_data]
        revenue_mean = sum(revenue_values) / len(revenue_values)
        revenue_std = (sum((x - revenue_mean) ** 2 for x in revenue_values) / len(revenue_values)) ** 0.5
        
        # Expense anomalies
        expense_values = [d.get("expenses", 0) for d in daily_data]
        expense_mean = sum(expense_values) / len(expense_values)
        expense_std = (sum((x - expense_mean) ** 2 for x in expense_values) / len(expense_values)) ** 0.5
        
        for day_data in daily_data:
            anomalies_found = []
            
            # Check revenue anomaly
            if revenue_std > 0:
                revenue_z = abs((day_data.get("revenue", 0) - revenue_mean) / revenue_std)
                if revenue_z > 2.5:  # Z-score threshold
                    anomalies_found.append({
                        "type": "revenue_spike" if day_data.get("revenue", 0) > revenue_mean else "revenue_drop",
                        "severity": "high" if revenue_z > 3 else "medium",
                        "z_score": revenue_z,
                        "value": day_data.get("revenue", 0),
                        "expected": revenue_mean
                    })
            
            # Check expense anomaly
            if expense_std > 0:
                expense_z = abs((day_data.get("expenses", 0) - expense_mean) / expense_std)
                if expense_z > 2.5:  # Z-score threshold
                    anomalies_found.append({
                        "type": "expense_spike" if day_data.get("expenses", 0) > expense_mean else "expense_drop",
                        "severity": "high" if expense_z > 3 else "medium",
                        "z_score": expense_z,
                        "value": day_data.get("expenses", 0),
                        "expected": expense_mean
                    })
            
            # Check for unusual transaction patterns
            transaction_count = day_data.get("transaction_count", 0)
            avg_count = sum(d.get("transaction_count", 0) for d in daily_data) / len(daily_data)
            if transaction_count > avg_count * 3:  # 3x normal transaction count
                anomalies_found.append({
                    "type": "high_transaction_volume",
                    "severity": "medium",
                    "transaction_count": transaction_count,
                    "average_count": avg_count
                })
            
            if anomalies_found:
                anomalies.append({
                    "date": day_data["_id"].isoformat(),
                    "anomalies": anomalies_found,
                    "total_amount": day_data.get("total_amount", 0),
                    "transaction_count": transaction_count
                })
        
        # Sort by date and return recent anomalies
        anomalies.sort(key=lambda x: x["date"], reverse=True)
        return anomalies[:10]  # Return top 10 recent anomalies
    
    async def get_dashboard_layout(self, user_id: str) -> Dict[str, Any]:
        """Get user's saved dashboard layout"""
        user = await users.find_one({"id": user_id})
        if not user:
            return self._get_default_layout()
        
        layout = user.get("dashboard_layout")
        if not layout:
            return self._get_default_layout()
        
        return layout
    
    async def save_dashboard_layout(self, user_id: str, layout: Dict[str, Any]) -> Dict[str, Any]:
        """Save user's dashboard layout"""
        await users.update_one(
            {"id": user_id},
            {"$set": {"dashboard_layout": layout, "updated_at": datetime.utcnow()}}
        )
        
        return layout
    
    def _calculate_trend_metrics(self, weekly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trend metrics from weekly data"""
        if len(weekly_data) < 4:
            return {
                "revenue_trend": "insufficient_data",
                "expense_trend": "insufficient_data",
                "net_trend": "insufficient_data"
            }
        
        # Calculate averages for recent vs previous periods
        recent_weeks = weekly_data[-4:]  # Last 4 weeks
        previous_weeks = weekly_data[-8:-4] if len(weekly_data) >= 8 else weekly_data[:-4]
        
        if not previous_weeks:
            return {
                "revenue_trend": "insufficient_data",
                "expense_trend": "insufficient_data",
                "net_trend": "insufficient_data"
            }
        
        recent_revenue_avg = sum(w.get("revenue", 0) for w in recent_weeks) / len(recent_weeks)
        previous_revenue_avg = sum(w.get("revenue", 0) for w in previous_weeks) / len(previous_weeks)
        
        recent_expense_avg = sum(w.get("expenses", 0) for w in recent_weeks) / len(recent_weeks)
        previous_expense_avg = sum(w.get("expenses", 0) for w in previous_weeks) / len(previous_weeks)
        
        recent_net_avg = sum(w.get("net", 0) for w in recent_weeks) / len(recent_weeks)
        previous_net_avg = sum(w.get("net", 0) for w in previous_weeks) / len(previous_weeks)
        
        # Calculate trends
        def calculate_trend(recent, previous):
            if previous == 0:
                return "stable" if recent == 0 else "increasing"
            change = (recent - previous) / previous
            if change > 0.1:
                return "increasing"
            elif change < -0.1:
                return "decreasing"
            else:
                return "stable"
        
        return {
            "revenue_trend": calculate_trend(recent_revenue_avg, previous_revenue_avg),
            "expense_trend": calculate_trend(recent_expense_avg, previous_expense_avg),
            "net_trend": calculate_trend(recent_net_avg, previous_net_avg),
            "revenue_change_percent": round(((recent_revenue_avg - previous_revenue_avg) / previous_revenue_avg * 100) if previous_revenue_avg > 0 else 0, 1),
            "expense_change_percent": round(((recent_expense_avg - previous_expense_avg) / previous_expense_avg * 100) if previous_expense_avg > 0 else 0, 1),
            "net_change_percent": round(((recent_net_avg - previous_net_avg) / previous_net_avg * 100) if previous_net_avg != 0 else 0, 1)
        }
    
    def _get_default_layout(self) -> Dict[str, Any]:
        """Get default dashboard layout"""
        return {
            "widgets": [
                {
                    "id": "overview",
                    "type": "overview_cards",
                    "position": {"x": 0, "y": 0, "w": 6, "h": 4},
                    "title": "Overview"
                },
                {
                    "id": "trends",
                    "type": "trends_chart",
                    "position": {"x": 6, "y": 0, "w": 6, "h": 4},
                    "title": "Revenue & Expense Trends"
                },
                {
                    "id": "cashflow_timeline",
                    "type": "cashflow_timeline",
                    "position": {"x": 0, "y": 4, "w": 12, "h": 4},
                    "title": "Cashflow Timeline"
                },
                {
                    "id": "top_customers",
                    "type": "top_customers",
                    "position": {"x": 0, "y": 8, "w": 6, "h": 3},
                    "title": "Top Customers"
                },
                {
                    "id": "anomalies",
                    "type": "anomalies",
                    "position": {"x": 6, "y": 8, "w": 6, "h": 3},
                    "title": "Recent Anomalies"
                }
            ],
            "layout": "grid"
        }


advanced_dashboard_service = AdvancedDashboardService()
