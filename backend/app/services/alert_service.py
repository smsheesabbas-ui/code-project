from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.core.database import get_database


class AlertService:
    """Financial alert detection and generation"""
    
    def __init__(self):
        self.cashflow_threshold_days = 30
        self.customer_concentration_threshold = 0.5  # 50%
        self.spending_spike_multiplier = 2.0  # 2x average
    
    async def check_user_alerts(self, user_id: str) -> List[Dict]:
        """Check for all types of alerts for a user"""
        alerts = []
        
        # Check cashflow risk
        cashflow_alert = await self._check_cashflow_risk(user_id)
        if cashflow_alert:
            alerts.append(cashflow_alert)
        
        # Check customer concentration
        concentration_alert = await self._check_customer_concentration(user_id)
        if concentration_alert:
            alerts.append(concentration_alert)
        
        # Check spending spikes
        spending_alert = await self._check_spending_spike(user_id)
        if spending_alert:
            alerts.append(spending_alert)
        
        return alerts
    
    async def _check_cashflow_risk(self, user_id: str) -> Optional[Dict]:
        """Check if projected cashflow might fall below threshold"""
        try:
            db = get_database()
            
            # Get current balance (simplified - sum of all transactions)
            current_balance_result = await db.transactions.aggregate([
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": None, "balance": {"$sum": "$amount"}}}
            ]).to_list(length=1)
            
            current_balance = current_balance_result[0]["balance"] if current_balance_result else 0
            
            # Get recent transactions to calculate daily burn rate
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_transactions = await db.transactions.find({
                "user_id": user_id,
                "transaction_date": {"$gte": thirty_days_ago}
            }).to_list(length=None)
            
            if len(recent_transactions) < 10:
                return None  # Not enough data
            
            # Calculate average daily change
            total_change = sum(t["amount"] for t in recent_transactions)
            daily_change = total_change / 30
            
            # Project cashflow for next 30 days
            projected_balance = current_balance + (daily_change * 30)
            
            # Check if projected balance is concerning
            if projected_balance < 0:
                return {
                    "type": "cashflow_risk",
                    "title": "Cashflow Risk Alert",
                    "message": f"Projected balance of ${projected_balance:.2f} in 30 days. Current daily change: ${daily_change:.2f}",
                    "severity": "high" if projected_balance < -1000 else "medium",
                    "data": {
                        "current_balance": current_balance,
                        "projected_balance": projected_balance,
                        "daily_change": daily_change,
                        "days_projection": 30
                    }
                }
            elif projected_balance < 1000:
                return {
                    "type": "cashflow_risk",
                    "title": "Low Cashflow Warning",
                    "message": f"Low projected balance of ${projected_balance:.2f} in 30 days. Consider reducing expenses.",
                    "severity": "low",
                    "data": {
                        "current_balance": current_balance,
                        "projected_balance": projected_balance,
                        "daily_change": daily_change,
                        "days_projection": 30
                    }
                }
            
            return None
            
        except Exception as e:
            print(f"Error checking cashflow risk: {e}")
            return None
    
    async def _check_customer_concentration(self, user_id: str) -> Optional[Dict]:
        """Check if revenue is too concentrated in one customer"""
        try:
            db = get_database()
            
            # Get revenue by customer (last 90 days)
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            
            pipeline = [
                {"$match": {
                    "user_id": user_id,
                    "transaction_date": {"$gte": ninety_days_ago},
                    "amount": {"$gte": 0}  # Revenue only
                }},
                {"$group": {
                    "_id": "$entity_name",
                    "total_revenue": {"$sum": "$amount"},
                    "transaction_count": {"$sum": 1}
                }},
                {"$sort": {"total_revenue": -1}},
                {"$limit": 10}
            ]
            
            customer_revenue = await db.transactions.aggregate(pipeline).to_list(length=None)
            
            if not customer_revenue or len(customer_revenue) < 2:
                return None  # Not enough customers or data
            
            # Calculate total revenue and concentration
            total_revenue = sum(c["total_revenue"] for c in customer_revenue)
            top_customer = customer_revenue[0]
            concentration_ratio = top_customer["total_revenue"] / total_revenue if total_revenue > 0 else 0
            
            if concentration_ratio > self.customer_concentration_threshold:
                return {
                    "type": "customer_concentration",
                    "title": "Customer Concentration Risk",
                    "message": f"{top_customer['_id']} accounts for {concentration_ratio:.1%} of your revenue ({top_customer['total_revenue']:.2f})",
                    "severity": "high" if concentration_ratio > 0.7 else "medium",
                    "data": {
                        "top_customer": top_customer["_id"],
                        "top_customer_revenue": top_customer["total_revenue"],
                        "concentration_ratio": concentration_ratio,
                        "total_revenue": total_revenue,
                        "customer_count": len(customer_revenue)
                    }
                }
            
            return None
            
        except Exception as e:
            print(f"Error checking customer concentration: {e}")
            return None
    
    async def _check_spending_spike(self, user_id: str) -> Optional[Dict]:
        """Check for unusual spending spikes in categories"""
        try:
            db = get_database()
            
            # Get spending by category for current period (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            sixty_days_ago = datetime.utcnow() - timedelta(days=60)
            
            # Current period spending
            current_pipeline = [
                {"$match": {
                    "user_id": user_id,
                    "transaction_date": {"$gte": thirty_days_ago},
                    "amount": {"$lt": 0}  # Expenses only
                }},
                {"$group": {
                    "_id": "$category",
                    "total_spent": {"$sum": {"$abs": "$amount"}},
                    "transaction_count": {"$sum": 1}
                }},
                {"$sort": {"total_spent": -1}}
            ]
            
            current_spending = await db.transactions.aggregate(current_pipeline).to_list(length=None)
            
            # Previous period spending (30-60 days ago)
            previous_pipeline = [
                {"$match": {
                    "user_id": user_id,
                    "transaction_date": {"$gte": sixty_days_ago, "$lt": thirty_days_ago},
                    "amount": {"$lt": 0}  # Expenses only
                }},
                {"$group": {
                    "_id": "$category",
                    "total_spent": {"$sum": {"$abs": "$amount"}},
                    "transaction_count": {"$sum": 1}
                }}
            ]
            
            previous_spending = await db.transactions.aggregate(previous_pipeline).to_list(length=None)
            
            # Create lookup for previous spending
            previous_lookup = {s["_id"]: s["total_spent"] for s in previous_spending}
            
            # Check for spikes
            spikes = []
            for current in current_spending:
                category = current["_id"]
                current_amount = current["total_spent"]
                previous_amount = previous_lookup.get(category, 0)
                
                # Only check if there was previous spending to compare
                if previous_amount > 0:
                    spike_ratio = current_amount / previous_amount
                    if spike_ratio > self.spending_spike_multiplier and current_amount > 100:  # Minimum $100 spike
                        spikes.append({
                            "category": category,
                            "current_amount": current_amount,
                            "previous_amount": previous_amount,
                            "spike_ratio": spike_ratio,
                            "increase_amount": current_amount - previous_amount
                        })
            
            if spikes:
                # Get the most significant spike
                biggest_spike = max(spikes, key=lambda x: x["spike_ratio"])
                
                return {
                    "type": "spending_spike",
                    "title": "Unusual Spending Spike",
                    "message": f"{biggest_spike['category']} spending increased by {biggest_spike['spike_ratio']:.1f}x (${biggest_spike['increase_amount']:.2f} increase)",
                    "severity": "high" if biggest_spike["spike_ratio"] > 3 else "medium",
                    "data": {
                        "category": biggest_spike["category"],
                        "current_amount": biggest_spike["current_amount"],
                        "previous_amount": biggest_spike["previous_amount"],
                        "spike_ratio": biggest_spike["spike_ratio"],
                        "increase_amount": biggest_spike["increase_amount"],
                        "all_spikes": spikes
                    }
                }
            
            return None
            
        except Exception as e:
            print(f"Error checking spending spikes: {e}")
            return None
    
    async def get_user_alerts(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get recent alerts for a user"""
        db = get_database()
        
        alerts = await db.alerts.find({
            "user_id": user_id
        }).sort("created_at", -1).limit(limit).to_list(length=None)
        
        # Convert ObjectId to string
        for alert in alerts:
            alert["id"] = str(alert["_id"])
            del alert["_id"]
        
        return alerts
    
    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Mark an alert as acknowledged"""
        try:
            db = get_database()
            
            result = await db.alerts.update_one(
                {"_id": alert_id, "user_id": user_id},
                {"$set": {"acknowledged": True, "acknowledged_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error acknowledging alert: {e}")
            return False


# Global instance
alert_service = AlertService()
