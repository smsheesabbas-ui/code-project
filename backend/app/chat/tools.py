from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from ..database import transactions, entities
from ..forecasting.prophet_service import prophet_service
from ..insights.service import insights_service


class ChatTools:
    """Data tools for chat assistant - all responses must be grounded in actual data"""
    
    @staticmethod
    async def get_revenue_summary(user_id: str, period: str = "month") -> Dict[str, Any]:
        """Get revenue summary for specified period"""
        # Calculate date range
        if period == "week":
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == "month":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == "quarter":
            start_date = datetime.utcnow() - timedelta(days=90)
        elif period == "year":
            start_date = datetime.utcnow() - timedelta(days=365)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$gt": 0},
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "average_transaction": {"$avg": "$amount"},
                "top_transaction": {"$max": "$amount"}
            }},
            {"$project": {
                "period": period,
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "transaction_count": "$transaction_count",
                "average_transaction": {"$round": ["$average_transaction", 2]},
                "top_transaction": {"$round": ["$top_transaction", 2]}
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "period": period,
                "total_revenue": 0.0,
                "transaction_count": 0,
                "average_transaction": 0.0,
                "top_transaction": 0.0,
                "message": f"No revenue data found for the {period}"
            }
        
        return result[0]
    
    @staticmethod
    async def get_expense_summary(user_id: str, period: str = "month") -> Dict[str, Any]:
        """Get expense summary for specified period"""
        # Calculate date range
        if period == "week":
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == "month":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == "quarter":
            start_date = datetime.utcnow() - timedelta(days=90)
        elif period == "year":
            start_date = datetime.utcnow() - timedelta(days=365)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$lt": 0},
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": None,
                "total_expenses": {"$sum": {"$abs": "$amount"}},
                "transaction_count": {"$sum": 1},
                "average_transaction": {"$avg": {"$abs": "$amount"}},
                "top_expense": {"$max": {"$abs": "$amount"}}
            }},
            {"$project": {
                "period": period,
                "total_expenses": {"$round": ["$total_expenses", 2]},
                "transaction_count": "$transaction_count",
                "average_transaction": {"$round": ["$average_transaction", 2]},
                "top_expense": {"$round": ["$top_expense", 2]}
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "period": period,
                "total_expenses": 0.0,
                "transaction_count": 0,
                "average_transaction": 0.0,
                "top_expense": 0.0,
                "message": f"No expense data found for the {period}"
            }
        
        return result[0]
    
    @staticmethod
    async def get_top_customer(user_id: str, period: str = "month") -> Dict[str, Any]:
        """Get top customer by revenue"""
        # Calculate date range
        if period == "week":
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == "month":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == "quarter":
            start_date = datetime.utcnow() - timedelta(days=90)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$gt": 0},
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": "$entity_name",
                "total_revenue": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "average_transaction": {"$avg": "$amount"}
            }},
            {"$match": {"total_revenue": {"$gt": 0}}},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 1},
            {"$project": {
                "customer_name": "$_id",
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "transaction_count": "$transaction_count",
                "average_transaction": {"$round": ["$average_transaction", 2]},
                "period": period
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "customer_name": "No customers found",
                "total_revenue": 0.0,
                "transaction_count": 0,
                "average_transaction": 0.0,
                "period": period,
                "message": f"No customer data found for the {period}"
            }
        
        return result[0]
    
    @staticmethod
    async def get_top_supplier(user_id: str, period: str = "month") -> Dict[str, Any]:
        """Get top supplier by expenses"""
        # Calculate date range
        if period == "week":
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == "month":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == "quarter":
            start_date = datetime.utcnow() - timedelta(days=90)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "amount": {"$lt": 0},
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": "$entity_name",
                "total_expenses": {"$sum": {"$abs": "$amount"}},
                "transaction_count": {"$sum": 1},
                "average_transaction": {"$avg": {"$abs": "$amount"}}
            }},
            {"$match": {"total_expenses": {"$gt": 0}}},
            {"$sort": {"total_expenses": -1}},
            {"$limit": 1},
            {"$project": {
                "supplier_name": "$_id",
                "total_expenses": {"$round": ["$total_expenses", 2]},
                "transaction_count": "$transaction_count",
                "average_transaction": {"$round": ["$average_transaction", 2]},
                "period": period
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "supplier_name": "No suppliers found",
                "total_expenses": 0.0,
                "transaction_count": 0,
                "average_transaction": 0.0,
                "period": period,
                "message": f"No supplier data found for the {period}"
            }
        
        return result[0]
    
    @staticmethod
    async def get_cashflow_summary(user_id: str, period: str = "month") -> Dict[str, Any]:
        """Get cashflow summary"""
        # Calculate date range
        if period == "week":
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == "month":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == "quarter":
            start_date = datetime.utcnow() - timedelta(days=90)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                "total_expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "net_cashflow": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1}
            }},
            {"$project": {
                "period": period,
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "total_expenses": {"$round": ["$total_expenses", 2]},
                "net_cashflow": {"$round": ["$net_cashflow", 2]},
                "transaction_count": "$transaction_count"
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "period": period,
                "total_revenue": 0.0,
                "total_expenses": 0.0,
                "net_cashflow": 0.0,
                "transaction_count": 0,
                "message": f"No cashflow data found for the {period}"
            }
        
        return result[0]
    
    @staticmethod
    async def get_trend_analysis(user_id: str, metric: str = "revenue") -> Dict[str, Any]:
        """Get trend analysis for specified metric"""
        # Get data for last 12 weeks
        start_date = datetime.utcnow() - timedelta(weeks=12)
        
        if metric == "revenue":
            amount_filter = {"$gt": ["$amount", 0]}
        elif metric == "expenses":
            amount_filter = {"$lt": ["$amount", 0]}
        else:
            amount_filter = {"$ne": ["$amount", None]}
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "transaction_date": {"$gte": start_date}
            }},
            {"$group": {
                "_id": {"$dateTrunc": {"date": "$transaction_date", "unit": "week"}},
                "weekly_total": {"$sum": {"$cond": [amount_filter, {"$abs": "$amount"}, 0]}},
                "transaction_count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
            {"$project": {
                "week": "$_id",
                "amount": {"$round": ["$weekly_total", 2]},
                "transaction_count": "$transaction_count"
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=None)
        
        if not result or len(result) < 2:
            return {
                "metric": metric,
                "trend": "insufficient_data",
                "data_points": len(result) if result else 0,
                "message": f"Insufficient data for {metric} trend analysis"
            }
        
        # Calculate trend
        recent_avg = sum(r["amount"] for r in result[-4:]) / 4  # Last 4 weeks
        previous_avg = sum(r["amount"] for r in result[-8:-4]) / 4  # Previous 4 weeks
        
        if recent_avg > previous_avg * 1.1:
            trend = "increasing"
            change_percent = ((recent_avg - previous_avg) / previous_avg) * 100
        elif recent_avg < previous_avg * 0.9:
            trend = "decreasing"
            change_percent = ((previous_avg - recent_avg) / previous_avg) * 100
        else:
            trend = "stable"
            change_percent = 0
        
        return {
            "metric": metric,
            "trend": trend,
            "change_percent": round(change_percent, 1),
            "recent_average": round(recent_avg, 2),
            "previous_average": round(previous_avg, 2),
            "data_points": len(result),
            "weekly_data": result[-8:]  # Last 8 weeks
        }
    
    @staticmethod
    async def get_entity_breakdown(user_id: str, entity_name: str) -> Dict[str, Any]:
        """Get breakdown for specific entity"""
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "entity_name": {"$regex": entity_name, "$options": "i"}
            }},
            {"$group": {
                "_id": "$entity_name",
                "total_amount": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                "expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "first_transaction": {"$min": "$transaction_date"},
                "last_transaction": {"$max": "$transaction_date"}
            }},
            {"$project": {
                "entity_name": "$_id",
                "total_amount": {"$round": ["$total_amount", 2]},
                "transaction_count": "$transaction_count",
                "revenue": {"$round": ["$revenue", 2]},
                "expenses": {"$round": ["$expenses", 2]},
                "first_transaction": "$first_transaction",
                "last_transaction": "$last_transaction"
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=None)
        
        if not result:
            return {
                "entity_name": entity_name,
                "message": f"No transactions found for entity: {entity_name}"
            }
        
        # Get recent transactions for this entity
        recent_pipeline = [
            {"$match": {
                "user_id": user_id,
                "entity_name": {"$regex": entity_name, "$options": "i"},
                "transaction_date": {"$gte": datetime.utcnow() - timedelta(days=30)}
            }},
            {"$sort": {"transaction_date": -1}},
            {"$limit": 10},
            {"$project": {
                "transaction_date": 1,
                "description": 1,
                "amount": {"$round": ["$amount", 2]},
                "category": 1
            }}
        ]
        
        recent_transactions = await transactions.aggregate(recent_pipeline).to_list(length=None)
        
        entity_data = result[0]
        entity_data["recent_transactions"] = recent_transactions
        
        return entity_data
    
    @staticmethod
    async def get_comparison_data(user_id: str, period1: str = "this_month", period2: str = "last_month") -> Dict[str, Any]:
        """Compare two periods"""
        # Calculate date ranges
        now = datetime.utcnow()
        
        if period1 == "this_month":
            start1 = now.replace(day=1)
            end1 = now
        elif period1 == "last_month":
            if now.month == 1:
                start1 = now.replace(year=now.year-1, month=12, day=1)
                end1 = now.replace(year=now.year-1, month=12, day=31)
            else:
                start1 = now.replace(month=now.month-1, day=1)
                end1 = now.replace(day=1) - timedelta(days=1)
        else:
            start1 = now - timedelta(days=30)
            end1 = now
        
        if period2 == "last_month":
            if now.month == 1:
                start2 = now.replace(year=now.year-1, month=12, day=1)
                end2 = now.replace(year=now.year-1, month=12, day=31)
            else:
                start2 = now.replace(month=now.month-1, day=1)
                end2 = now.replace(day=1) - timedelta(days=1)
        else:
            start2 = start1 - timedelta(days=30)
            end2 = start1
        
        # Get data for both periods
        async def get_period_data(start_date, end_date, period_name):
            pipeline = [
                {"$match": {
                    "user_id": user_id,
                    "transaction_date": {"$gte": start_date, "$lte": end_date}
                }},
                {"$group": {
                    "_id": None,
                    "revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                    "expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                    "net": {"$sum": "$amount"},
                    "transactions": {"$sum": 1}
                }},
                {"$project": {
                    "period": period_name,
                    "revenue": {"$round": ["$revenue", 2]},
                    "expenses": {"$round": ["$expenses", 2]},
                    "net": {"$round": ["$net", 2]},
                    "transactions": "$transactions"
                }}
            ]
            
            result = await transactions.aggregate(pipeline).to_list(length=1)
            return result[0] if result else {
                "period": period_name,
                "revenue": 0.0,
                "expenses": 0.0,
                "net": 0.0,
                "transactions": 0
            }
        
        period1_data = await get_period_data(start1, end1, period1)
        period2_data = await get_period_data(start2, end2, period2)
        
        # Calculate changes
        revenue_change = ((period1_data["revenue"] - period2_data["revenue"]) / period2_data["revenue"] * 100) if period2_data["revenue"] > 0 else 0
        expenses_change = ((period1_data["expenses"] - period2_data["expenses"]) / period2_data["expenses"] * 100) if period2_data["expenses"] > 0 else 0
        net_change = period1_data["net"] - period2_data["net"]
        
        return {
            "period1": period1_data,
            "period2": period2_data,
            "revenue_change_percent": round(revenue_change, 1),
            "expenses_change_percent": round(expenses_change, 1),
            "net_change": round(net_change, 2)
        }


chat_tools = ChatTools()
