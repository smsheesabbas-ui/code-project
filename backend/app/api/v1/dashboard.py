from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.database import get_database
from bson import ObjectId
from pydantic import BaseModel
from decimal import Decimal

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class OverviewResponse(BaseModel):
    current_cash_balance: float
    total_revenue_this_month: float
    total_expenses_this_month: float
    net_income_this_month: float
    total_revenue_last_month: float
    total_expenses_last_month: float
    net_income_last_month: float
    revenue_change_percent: float
    expense_change_percent: float


class TopEntityResponse(BaseModel):
    id: str
    name: str
    entity_type: str
    total_amount: float
    transaction_count: int


@router.get("/overview")
async def get_dashboard_overview():
    """Get dashboard overview - no auth required for demo"""
    db = get_database()
    
    # Use demo user data
    demo_user_id = "69a235b64db7304c81b42977"  # Our demo user ID
    
    # Get transactions for demo user
    transactions = await db.transactions.find({"user_id": demo_user_id}).to_list(length=100)
    
    # Calculate basic metrics
    total_income = sum(tx["amount"] for tx in transactions if tx["amount"] > 0)
    total_expenses = sum(abs(tx["amount"]) for tx in transactions if tx["amount"] < 0)
    net_balance = total_income - total_expenses
    
    # Recent transactions
    recent_transactions = sorted(transactions, key=lambda x: x["transaction_date"], reverse=True)[:5]
    current_month_pipeline = [
        {"$match": current_month_filter},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
            "total_expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
            "net_income": {"$sum": "$amount"},
            "last_balance": {"$last": "$balance"}
        }}
    ]
    
    current_month_result = await db.transactions.aggregate(current_month_pipeline).to_list(length=1)
    current_month_data = current_month_result[0] if current_month_result else {
        "total_revenue": 0,
        "total_expenses": 0,
        "net_income": 0,
        "last_balance": 0
    }
    
    # Calculate last month metrics
    last_month_pipeline = [
        {"$match": last_month_filter},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
            "total_expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
            "net_income": {"$sum": "$amount"}
        }}
    ]
    
    last_month_result = await db.transactions.aggregate(last_month_pipeline).to_list(length=1)
    last_month_data = last_month_result[0] if last_month_result else {
        "total_revenue": 0,
        "total_expenses": 0,
        "net_income": 0
    }
    
    # Calculate percentage changes
    revenue_change = calculate_percent_change(
        last_month_data["total_revenue"],
        current_month_data["total_revenue"]
    )
    
    expense_change = calculate_percent_change(
        last_month_data["total_expenses"],
        current_month_data["total_expenses"]
    )
    
    return OverviewResponse(
        current_cash_balance=current_month_data["last_balance"] or 0,
        total_revenue_this_month=current_month_data["total_revenue"],
        total_expenses_this_month=current_month_data["total_expenses"],
        net_income_this_month=current_month_data["net_income"],
        total_revenue_last_month=last_month_data["total_revenue"],
        total_expenses_last_month=last_month_data["total_expenses"],
        net_income_last_month=last_month_data["net_income"],
        revenue_change_percent=revenue_change,
        expense_change_percent=expense_change
    )


@router.get("/top-customers", response_model=List[TopEntityResponse])
async def get_top_customers(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get top customers by total amount"""
    db = get_database()
    
    pipeline = [
        {
            "$match": {
                "user_id": current_user.id,
                "amount": {"$gt": 0}  # Revenue only
            }
        },
        {
            "$group": {
                "_id": "$entity_id",
                "total_amount": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "description": {"$first": "$description"}
            }
        },
        {"$sort": {"total_amount": -1}},
        {"$limit": limit}
    ]
    
    results = await db.transactions.aggregate(pipeline).to_list(length=limit)
    
    top_customers = []
    for result in results:
        if result["_id"]:
            # Get entity details
            entity = await db.entities.find_one({"_id": result["_id"]})
            if entity:
                top_customers.append(TopEntityResponse(
                    id=str(entity["_id"]),
                    name=entity["name"],
                    entity_type=entity["entity_type"],
                    total_amount=result["total_amount"],
                    transaction_count=result["transaction_count"]
                ))
    
    return top_customers


@router.get("/top-suppliers", response_model=List[TopEntityResponse])
async def get_top_suppliers(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get top suppliers by total amount"""
    db = get_database()
    
    pipeline = [
        {
            "$match": {
                "user_id": current_user.id,
                "amount": {"$lt": 0}  # Expenses only
            }
        },
        {
            "$group": {
                "_id": "$entity_id",
                "total_amount": {"$sum": {"$abs": "$amount"}},
                "transaction_count": {"$sum": 1},
                "description": {"$first": "$description"}
            }
        },
        {"$sort": {"total_amount": -1}},
        {"$limit": limit}
    ]
    
    results = await db.transactions.aggregate(pipeline).to_list(length=limit)
    
    top_suppliers = []
    for result in results:
        if result["_id"]:
            # Get entity details
            entity = await db.entities.find_one({"_id": result["_id"]})
            if entity:
                top_suppliers.append(TopEntityResponse(
                    id=str(entity["_id"]),
                    name=entity["name"],
                    entity_type=entity["entity_type"],
                    total_amount=result["total_amount"],
                    transaction_count=result["transaction_count"]
                ))
    
    return top_suppliers


@router.get("/monthly-trend")
async def get_monthly_trend(
    months: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_user)
):
    """Get monthly revenue and expense trend"""
    db = get_database()
    
    # Calculate date range
    today = datetime.utcnow().date()
    start_date = date(today.year, today.month - months + 1, 1)
    if start_date.month > today.month:
        start_date = date(today.year - 1, start_date.month, 1)
    
    pipeline = [
        {
            "$match": {
                "user_id": current_user.id,
                "transaction_date": {"$gte": datetime.combine(start_date, datetime.min.time())}
            }
        },
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$transaction_date"},
                    "month": {"$month": "$transaction_date"}
                },
                "revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                "expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "net_income": {"$sum": "$amount"}
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    
    results = await db.transactions.aggregate(pipeline).to_list(length=months)
    
    # Format results
    trend_data = []
    for result in results:
        year = result["_id"]["year"]
        month = result["_id"]["month"]
        month_name = datetime(year, month, 1).strftime("%B %Y")
        
        trend_data.append({
            "month": month_name,
            "year": year,
            "month_number": month,
            "revenue": result["revenue"],
            "expenses": result["expenses"],
            "net_income": result["net_income"]
        })
    
    return {"trend": trend_data}


def calculate_percent_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change"""
    if old_value == 0:
        return 100.0 if new_value > 0 else 0.0
    
    return ((new_value - old_value) / old_value) * 100
