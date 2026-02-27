from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from ..database import transactions, entities
from ..models.transaction import Transaction
from ..models.entity import EntitySummary

class DashboardService:
    async def get_overview(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard overview"""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get all transactions for user
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_balance": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "this_month_revenue": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$gte": ["$transaction_date", month_start]},
                                {"$gt": ["$amount", 0]}
                            ]},
                            "$amount",
                            0
                        ]
                    }
                },
                "this_month_expense": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$gte": ["$transaction_date", month_start]},
                                {"$lt": ["$amount", 0]}
                            ]},
                            {"$abs": "$amount"},
                            0
                        ]
                    }
                }
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if result:
            data = result[0]
            return {
                "cash_balance": float(data.get("total_balance", 0)),
                "total_revenue_this_month": float(data.get("this_month_revenue", 0)),
                "total_expenses_this_month": float(data.get("this_month_expense", 0)),
                "net_income_this_month": float(
                    data.get("this_month_revenue", 0) - data.get("this_month_expense", 0)
                ),
                "total_transactions": data.get("transaction_count", 0)
            }
        else:
            return {
                "cash_balance": 0.0,
                "total_revenue_this_month": 0.0,
                "total_expenses_this_month": 0.0,
                "net_income_this_month": 0.0,
                "total_transactions": 0
            }

    async def get_top_customers(self, user_id: str, limit: int = 10) -> List[EntitySummary]:
        """Get top customers by revenue"""
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "amount": {"$gt": 0}
                }
            },
            {
                "$group": {
                    "_id": "$description",
                    "total_amount": {"$sum": "$amount"},
                    "transaction_count": {"$sum": 1}
                }
            },
            {"$sort": {"total_amount": -1}},
            {"$limit": limit}
        ]
        
        results = await transactions.aggregate(pipeline).to_list(length=limit)
        
        return [
            EntitySummary(
                id=result["_id"],
                name=result["_id"],
                entity_type="customer",
                total_amount=Decimal(str(result["total_amount"])),
                transaction_count=result["transaction_count"]
            )
            for result in results
        ]

    async def get_top_suppliers(self, user_id: str, limit: int = 10) -> List[EntitySummary]:
        """Get top suppliers by expenses"""
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "amount": {"$lt": 0}
                }
            },
            {
                "$group": {
                    "_id": "$description",
                    "total_amount": {"$sum": {"$abs": "$amount"}},
                    "transaction_count": {"$sum": 1}
                }
            },
            {"$sort": {"total_amount": -1}},
            {"$limit": limit}
        ]
        
        results = await transactions.aggregate(pipeline).to_list(length=limit)
        
        return [
            EntitySummary(
                id=result["_id"],
                name=result["_id"],
                entity_type="supplier",
                total_amount=Decimal(str(result["total_amount"])),
                transaction_count=result["transaction_count"]
            )
            for result in results
        ]

    async def get_transactions(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        entity_id: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get transactions with filtering and pagination"""
        # Build filter
        filter_query = {"user_id": user_id}
        
        if start_date:
            filter_query["transaction_date"] = {"$gte": start_date}
        
        if end_date:
            if "transaction_date" in filter_query:
                filter_query["transaction_date"]["$lte"] = end_date
            else:
                filter_query["transaction_date"] = {"$lte": end_date}
        
        if entity_id:
            filter_query["description"] = entity_id
        
        # Get total count
        total = await transactions.count_documents(filter_query)
        
        # Get transactions with pagination
        skip = (page - 1) * limit
        cursor = transactions.find(filter_query).sort("transaction_date", -1).skip(skip).limit(limit)
        
        transaction_list = []
        async for doc in cursor:
            transaction_list.append(Transaction(**doc))
        
        return {
            "transactions": transaction_list,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }

dashboard_service = DashboardService()
