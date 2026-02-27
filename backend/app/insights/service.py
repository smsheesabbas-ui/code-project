from datetime import datetime, timedelta
from typing import Dict, Any, List
from ..database import transactions, entities
from ..ai.groq_client import get_groq_client


class InsightsService:
    def __init__(self):
        self.groq_client = get_groq_client()
    
    async def get_weekly_summary(self, user_id: str) -> Dict[str, Any]:
        """Generate AI-powered weekly summary"""
        
        # Get weekly data
        weekly_data = await self._get_weekly_financial_data(user_id)
        
        if weekly_data["transaction_count"] == 0:
            return {
                "status": "no_data",
                "message": "No transaction data for this week",
                "summary": "No financial activity to summarize this week."
            }
        
        # Generate AI summary
        ai_summary = await self.groq_client.generate_weekly_summary(weekly_data)
        
        # Generate recommendations
        recommendations = await self.groq_client.generate_recommendations(
            await self._get_financial_health_metrics(user_id)
        )
        
        return {
            "status": "success",
            "period": {
                "start": weekly_data["period_start"],
                "end": weekly_data["period_end"]
            },
            "financial_data": weekly_data,
            "ai_summary": ai_summary,
            "recommendations": recommendations
        }
    
    async def _get_weekly_financial_data(self, user_id: str) -> Dict[str, Any]:
        """Get financial data for the current week"""
        
        # Calculate week boundaries (Sunday to Saturday)
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday() + 1)  # Previous Sunday
        week_end = week_start + timedelta(days=6)  # Saturday
        
        # Get transactions for the week
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "transaction_date": {
                    "$gte": datetime.combine(week_start, datetime.min.time()),
                    "$lte": datetime.combine(week_end, datetime.max.time())
                }
            }},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                "total_expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "transaction_count": {"$sum": 1}
            }},
            {"$project": {
                "total_revenue": {"$ifNull": ["$total_revenue", 0]},
                "total_expenses": {"$ifNull": ["$total_expenses", 0]},
                "transaction_count": {"$ifNull": ["$transaction_count", 0]},
                "net_income": {"$subtract": [
                    {"$ifNull": ["$total_revenue", 0]},
                    {"$ifNull": ["$total_expenses", 0]}
                ]}
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "period_start": week_start.isoformat(),
                "period_end": week_end.isoformat(),
                "total_revenue": 0,
                "total_expenses": 0,
                "net_income": 0,
                "transaction_count": 0,
                "top_customer": "N/A",
                "top_expense_category": "N/A"
            }
        
        data = result[0]
        
        # Get top customer and expense category
        top_customer = await self._get_top_customer(user_id, week_start, week_end)
        top_expense_category = await self._get_top_expense_category(user_id, week_start, week_end)
        
        return {
            "period_start": week_start.isoformat(),
            "period_end": week_end.isoformat(),
            "total_revenue": data["total_revenue"],
            "total_expenses": data["total_expenses"],
            "net_income": data["net_income"],
            "transaction_count": data["transaction_count"],
            "top_customer": top_customer,
            "top_expense_category": top_expense_category
        }
    
    async def _get_top_customer(self, user_id: str, start_date: datetime.date, end_date: datetime.date) -> str:
        """Get top customer for the period"""
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$gt": 0},
                "transaction_date": {
                    "$gte": datetime.combine(start_date, datetime.min.time()),
                    "$lte": datetime.combine(end_date, datetime.max.time())
                }
            }},
            {"$group": {
                "_id": "$entity_name",
                "total_amount": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1}
            }},
            {"$match": {"total_amount": {"$gt": 0}}},
            {"$sort": {"total_amount": -1}},
            {"$limit": 1}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        return result[0]["_id"] if result and result[0]["_id"] else "N/A"
    
    async def _get_top_expense_category(self, user_id: str, start_date: datetime.date, end_date: datetime.date) -> str:
        """Get top expense category for the period"""
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$lt": 0},
                "transaction_date": {
                    "$gte": datetime.combine(start_date, datetime.min.time()),
                    "$lte": datetime.combine(end_date, datetime.max.time())
                }
            }},
            {"$group": {
                "_id": "$category",
                "total_amount": {"$sum": {"$abs": "$amount"}},
                "transaction_count": {"$sum": 1}
            }},
            {"$match": {"total_amount": {"$gt": 0}}},
            {"$sort": {"total_amount": -1}},
            {"$limit": 1}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        return result[0]["_id"] if result and result[0]["_id"] else "N/A"
    
    async def _get_financial_health_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get financial health metrics for recommendations"""
        
        # Get current cash balance (simplified)
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_balance": {"$sum": "$amount"},
                "monthly_revenue": {"$sum": {
                    "$cond": [
                        {"$and": [
                            {"$gt": ["$amount", 0]},
                            {"$gte": ["$transaction_date", datetime.utcnow() - timedelta(days=30)]}
                        ]},
                        "$amount",
                        0
                    ]
                }},
                "monthly_expenses": {"$sum": {
                    "$cond": [
                        {"$and": [
                            {"$lt": ["$amount", 0]},
                            {"$gte": ["$transaction_date", datetime.utcnow() - timedelta(days=30)]}
                        ]},
                        {"$abs": "$amount"},
                        0
                    ]
                }}
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "cash_balance": 0,
                "monthly_burn": 0,
                "revenue_growth": 0,
                "top_expense": "N/A",
                "customer_concentration": 0
            }
        
        data = result[0]
        
        # Calculate additional metrics
        monthly_burn = data["monthly_expenses"]
        cash_balance = data["total_balance"]
        
        # Revenue growth (compare to previous month)
        revenue_growth = await self._calculate_revenue_growth(user_id)
        
        # Top expense
        top_expense = await self._get_top_expense_category(
            user_id,
            datetime.utcnow().date() - timedelta(days=30),
            datetime.utcnow().date()
        )
        
        # Customer concentration
        customer_concentration = await self._calculate_customer_concentration(user_id)
        
        return {
            "cash_balance": cash_balance,
            "monthly_burn": monthly_burn,
            "revenue_growth": revenue_growth,
            "top_expense": top_expense,
            "customer_concentration": customer_concentration
        }
    
    async def _calculate_revenue_growth(self, user_id: str) -> float:
        """Calculate month-over-month revenue growth"""
        
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=32)).replace(day=1)
        
        # Get revenue for current month
        current_pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$gt": 0},
                "transaction_date": {"$gte": current_month_start}
            }},
            {"$group": {"_id": None, "revenue": {"$sum": "$amount"}}}
        ]
        
        # Get revenue for last month
        last_pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$gt": 0},
                "transaction_date": {
                    "$gte": last_month_start,
                    "$lt": current_month_start
                }
            }},
            {"$group": {"_id": None, "revenue": {"$sum": "$amount"}}}
        ]
        
        current_result = await transactions.aggregate(current_pipeline).to_list(length=1)
        last_result = await transactions.aggregate(last_pipeline).to_list(length=1)
        
        current_revenue = current_result[0]["revenue"] if current_result else 0
        last_revenue = last_result[0]["revenue"] if last_result else 0
        
        if last_revenue == 0:
            return 0.0 if current_revenue == 0 else 100.0
        
        growth = ((current_revenue - last_revenue) / last_revenue) * 100
        return round(growth, 1)
    
    async def _calculate_customer_concentration(self, user_id: str) -> float:
        """Calculate customer concentration (percentage of revenue from top customer)"""
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$gt": 0},
                "transaction_date": {"$gte": datetime.utcnow() - timedelta(days=30)}
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
            return 0.0
        
        top_customer_revenue = result[0]["total_revenue"]
        
        # Get total revenue
        total_pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$gt": 0},
                "transaction_date": {"$gte": datetime.utcnow() - timedelta(days=30)}
            }},
            {"$group": {"_id": None, "total_revenue": {"$sum": "$amount"}}}
        ]
        
        total_result = await transactions.aggregate(total_pipeline).to_list(length=1)
        total_revenue = total_result[0]["total_revenue"] if total_result else 0
        
        if total_revenue == 0:
            return 0.0
        
        concentration = (top_customer_revenue / total_revenue) * 100
        return round(concentration, 1)


insights_service = InsightsService()
