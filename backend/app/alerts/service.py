import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from ..database import alerts, transactions, users
from ..forecasting.prophet_service import prophet_service


class AlertService:
    def __init__(self):
        pass
    
    async def check_user_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Check and create alerts for a user"""
        new_alerts = []
        
        # Check cashflow risk
        cashflow_alert = await self._check_cashflow_risk(user_id)
        if cashflow_alert:
            new_alerts.append(cashflow_alert)
        
        # Check customer concentration
        concentration_alert = await self._check_customer_concentration(user_id)
        if concentration_alert:
            new_alerts.append(concentration_alert)
        
        # Check spending spikes
        spending_alert = await self._check_spending_spike(user_id)
        if spending_alert:
            new_alerts.append(spending_alert)
        
        return new_alerts
    
    async def _check_cashflow_risk(self, user_id: str) -> Dict[str, Any]:
        """Check for cashflow risk using forecast"""
        
        # Get forecast
        forecast_result = await prophet_service.generate_cashflow_forecast(user_id, days=30)
        
        if forecast_result["status"] != "success":
            return None
        
        forecast = forecast_result["forecast"]
        metrics = forecast_result["metrics"]
        
        # Check if projected balance goes below threshold
        threshold = 1000.0  # Configurable threshold
        min_balance = min(f["predicted_amount"] for f in forecast)
        
        if min_balance < threshold:
            # Find when it goes below threshold
            below_threshold_date = None
            for f in forecast:
                if f["predicted_amount"] < threshold:
                    below_threshold_date = f["date"]
                    break
            
            return await self._create_alert(
                user_id=user_id,
                alert_type="cashflow_risk",
                severity="high" if min_balance < 0 else "medium",
                title="Cashflow Risk Alert",
                message=f"Projected balance will drop below ${threshold:.0f} on {below_threshold_date[:10] if below_threshold_date else 'unknown date'}. Current risk level: {metrics['cashflow_risk']}.",
                data={
                    "projected_balance": metrics["projected_balance"],
                    "min_balance": min_balance,
                    "threshold": threshold,
                    "risk_level": metrics["cashflow_risk"]
                }
            )
        
        return None
    
    async def _check_customer_concentration(self, user_id: str) -> Dict[str, Any]:
        """Check for customer concentration risk"""
        
        # Calculate customer concentration
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$gt": 0},
                "transaction_date": {"$gte": datetime.utcnow() - timedelta(days=90)}
            }},
            {"$group": {
                "_id": "$entity_name",
                "total_revenue": {"$sum": "$amount"}
            }},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 1}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return None
        
        top_customer = result[0]
        
        # Get total revenue
        total_pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$gt": 0},
                "transaction_date": {"$gte": datetime.utcnow() - timedelta(days=90)}
            }},
            {"$group": {"_id": None, "total_revenue": {"$sum": "$amount"}}}
        ]
        
        total_result = await transactions.aggregate(total_pipeline).to_list(length=1)
        
        if not total_result or total_result[0]["total_revenue"] == 0:
            return None
        
        total_revenue = total_result[0]["total_revenue"]
        concentration = (top_customer["total_revenue"] / total_revenue) * 100
        
        if concentration > 50:  # Alert if single customer > 50% of revenue
            severity = "high" if concentration > 75 else "medium"
            
            return await self._create_alert(
                user_id=user_id,
                alert_type="customer_concentration",
                severity=severity,
                title="Customer Concentration Alert",
                message=f"Customer '{top_customer['_id']}' represents {concentration:.1f}% of your revenue. Consider diversifying your customer base.",
                data={
                    "customer_name": top_customer["_id"],
                    "concentration_percentage": concentration,
                    "customer_revenue": top_customer["total_revenue"],
                    "total_revenue": total_revenue
                }
            )
        
        return None
    
    async def _check_spending_spike(self, user_id: str) -> Dict[str, Any]:
        """Check for spending spikes in categories"""
        
        # Get spending by category for last 30 days vs previous 30 days
        current_period = datetime.utcnow() - timedelta(days=30)
        previous_period = datetime.utcnow() - timedelta(days=60)
        
        # Current period spending
        current_pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$lt": 0},
                "transaction_date": {"$gte": current_period}
            }},
            {"$group": {
                "_id": "$category",
                "total_spending": {"$sum": {"$abs": "$amount"}},
                "transaction_count": {"$sum": 1}
            }},
            {"$match": {"total_spending": {"$gt": 0}}}
        ]
        
        # Previous period spending
        previous_pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$lt": 0},
                "transaction_date": {
                    "$gte": previous_period,
                    "$lt": current_period
                }
            }},
            {"$group": {
                "_id": "$category",
                "total_spending": {"$sum": {"$abs": "$amount"}},
                "transaction_count": {"$sum": 1}
            }},
            {"$match": {"total_spending": {"$gt": 0}}}
        ]
        
        current_results = await transactions.aggregate(current_pipeline).to_list(length=None)
        previous_results = await transactions.aggregate(previous_pipeline).to_list(length=None)
        
        # Create lookup for previous period
        previous_lookup = {r["_id"]: r["total_spending"] for r in previous_results}
        
        # Check for spikes
        for current in current_results:
            category = current["_id"]
            current_spending = current["total_spending"]
            previous_spending = previous_lookup.get(category, 0)
            
            # Only check if there was previous spending
            if previous_spending > 0:
                increase_percentage = ((current_spending - previous_spending) / previous_spending) * 100
                
                if increase_percentage > 200:  # Alert if spending increased by > 200%
                    severity = "high" if increase_percentage > 500 else "medium"
                    
                    return await self._create_alert(
                        user_id=user_id,
                        alert_type="spending_spike",
                        severity=severity,
                        title="Spending Spike Alert",
                        message=f"Spending in '{category}' increased by {increase_percentage:.0f}% this month (${current_spending:.2f} vs ${previous_spending:.2f} last month).",
                        data={
                            "category": category,
                            "increase_percentage": increase_percentage,
                            "current_spending": current_spending,
                            "previous_spending": previous_spending,
                            "transaction_count": current["transaction_count"]
                        }
                    )
        
        return None
    
    async def _create_alert(self, user_id: str, alert_type: str, severity: str, title: str, message: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert"""
        
        # Check if similar alert already exists and is not acknowledged
        existing = await alerts.find_one({
            "user_id": user_id,
            "type": alert_type,
            "status": "active",
            "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
        })
        
        if existing:
            return None  # Don't create duplicate alerts within 24 hours
        
        alert = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": alert_type,
            "severity": severity,
            "status": "active",
            "title": title,
            "message": message,
            "data": data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await alerts.insert_one(alert)
        return alert
    
    async def get_active_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active alerts for user"""
        
        cursor = alerts.find({
            "user_id": user_id,
            "status": "active"
        }).sort("created_at", -1)
        
        alerts_list = []
        async for doc in cursor:
            alerts_list.append(doc)
        
        return alerts_list
    
    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert"""
        
        result = await alerts.update_one(
            {"id": alert_id, "user_id": user_id},
            {"$set": {
                "status": "acknowledged",
                "acknowledged_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0
    
    async def dismiss_alert(self, alert_id: str, user_id: str) -> bool:
        """Dismiss an alert"""
        
        result = await alerts.update_one(
            {"id": alert_id, "user_id": user_id},
            {"$set": {
                "status": "dismissed",
                "dismissed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0


alert_service = AlertService()
