from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from app.core.database import get_database
from app.services.ai_service import ai_service
from app.services.forecasting_service import forecasting_service
from app.services.alert_service import alert_service
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# Demo mode - use hardcoded user ID
DEMO_USER_ID = "69a235b64db7304c81b42977"


@router.get("/weekly-summary")
async def get_weekly_summary():
    """Get AI-generated weekly financial summary - Demo Mode"""
    try:
        # Get user's weekly data
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        db = get_database()
        
        # Aggregate weekly data
        pipeline = [
            {"$match": {
                "user_id": DEMO_USER_ID,
                "transaction_date": {"$gte": week_ago}
            }},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": {"$cond": [{"$gte": ["$amount", 0]}, "$amount", 0]}},
                "total_expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "transaction_count": {"$sum": 1},
                "top_customer": {"$max": "$entity_name"},
                "top_expense_category": {"$max": "$category"}
            }}
        ]
        
        result = await db.transactions.aggregate(pipeline).to_list(length=1)
        weekly_data = result[0] if result else {
            "total_revenue": 0,
            "total_expenses": 0,
            "transaction_count": 0,
            "top_customer": None,
            "top_expense_category": None
        }
        
        # Generate AI summary
        try:
            summary = await ai_service.generate_weekly_summary(weekly_data)
        except Exception as e:
            print(f"AI Service Error: {e}")
            summary = None
        
        # Check if we have a valid summary or if there's an API key issue
        if not summary:
            if ai_service.client:
                # API key exists but failed (invalid key, network issues, etc.)
                summary = "AI service temporarily unavailable. Please check API key configuration."
            else:
                # No API key configured
                summary = "Demo mode: AI summary not available without GROQ_API_KEY"
        
        return {
            "summary": summary,
            "data": weekly_data,
            "period_start": week_ago.isoformat(),
            "period_end": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error in weekly summary: {e}")
        return {
            "summary": f"Error generating summary: {str(e)}",
            "data": {"total_revenue": 0, "total_expenses": 0, "transaction_count": 0},
            "period_start": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "error": True
        }


@router.get("/recommendations")
async def get_recommendations():
    """Get AI-powered financial recommendations - Demo Mode"""
    try:
        # Get user's data for recommendations
        db = get_database()
        
        # Get last 30 days of data
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {"$match": {
                "user_id": DEMO_USER_ID,
                "transaction_date": {"$gte": thirty_days_ago}
            }},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": {"$cond": [{"$gte": ["$amount", 0]}, "$amount", 0]}},
                "total_expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "transaction_count": {"$sum": 1}
            }}
        ]
        
        result = await db.transactions.aggregate(pipeline).to_list(length=1)
        user_data = result[0] if result else {
            "total_revenue": 0,
            "total_expenses": 0,
            "transaction_count": 0
        }
        
        # Add top expense category
        expense_pipeline = [
            {"$match": {
                "user_id": DEMO_USER_ID,
                "transaction_date": {"$gte": thirty_days_ago},
                "amount": {"$lt": 0}
            }},
            {"$group": {
                "_id": "$category",
                "total_amount": {"$sum": {"$abs": "$amount"}}
            }},
            {"$sort": {"total_amount": -1}},
            {"$limit": 1}
        ]
        
        expense_result = await db.transactions.aggregate(expense_pipeline).to_list(length=1)
        if expense_result:
            user_data["top_expense_category"] = expense_result[0]["_id"]
            user_data["top_expense_amount"] = expense_result[0]["total_amount"]
        
        # Calculate customer concentration
        revenue_pipeline = [
            {"$match": {
                "user_id": DEMO_USER_ID,
                "transaction_date": {"$gte": thirty_days_ago},
                "amount": {"$gte": 0}
            }},
            {"$group": {
                "_id": "$entity_name",
                "total_revenue": {"$sum": "$amount"}
            }},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 1}
        ]
        
        revenue_result = await db.transactions.aggregate(revenue_pipeline).to_list(length=1)
        if revenue_result and user_data.get("total_revenue", 0) > 0:
            user_data["customer_concentration"] = revenue_result[0]["total_revenue"] / user_data["total_revenue"]
        
        # Generate recommendations
        try:
            recommendations = await ai_service.generate_recommendations(user_data)
        except Exception as e:
            print(f"AI Service Error: {e}")
            recommendations = None
        
        return {
            "recommendations": recommendations or [
                "Demo mode: Set up GROQ_API_KEY to get AI-powered recommendations",
                "Consider tracking expenses more consistently",
                "Review your largest expense categories for optimization opportunities"
            ],
            "data": user_data,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error in recommendations: {e}")
        return {
            "recommendations": [f"Error generating recommendations: {str(e)}"],
            "data": {"total_revenue": 0, "total_expenses": 0, "transaction_count": 0},
            "generated_at": datetime.utcnow().isoformat(),
            "error": True
        }


@router.get("/forecasts/cashflow")
async def get_cashflow_forecast(days: int = 30):
    """Get cashflow forecast using Prophet - Demo Mode"""
    try:
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Forecast days must be between 1 and 365"
            )
        
        forecast = await forecasting_service.generate_forecast(DEMO_USER_ID, days)
        
        return forecast
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forecast: {str(e)}"
        )


@router.get("/alerts")
async def get_alerts(limit: int = 50):
    """Get user's financial alerts - Demo Mode"""
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        try:
            alerts = await alert_service.get_user_alerts(DEMO_USER_ID, limit)
        except Exception as e:
            print(f"Alert Service Error: {e}")
            alerts = []
        
        return {
            "alerts": alerts,
            "count": len(alerts)
        }
        
    except Exception as e:
        print(f"Error in alerts: {e}")
        return {
            "alerts": [{"type": "error", "message": f"Error generating alerts: {str(e)}"}],
            "count": 1,
            "error": True
        }


@router.post("/alerts/check")
async def check_alerts():
    """Manually trigger alert checking for user - Demo Mode"""
    try:
        alerts = await alert_service.check_user_alerts(DEMO_USER_ID)
        
        return {
            "alerts_found": len(alerts),
            "alerts": alerts,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check alerts: {str(e)}"
        )


@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert - Demo Mode"""
    try:
        success = await alert_service.acknowledge_alert(alert_id, DEMO_USER_ID)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found or already acknowledged"
            )
        
        return {
            "message": "Alert acknowledged successfully",
            "alert_id": alert_id,
            "acknowledged_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.post("/extract-entity")
async def extract_entity(request: dict):
    """Extract entity name from transaction description using AI - Demo Mode"""
    try:
        description = request.get("description", "")
        
        if not description or not description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Description cannot be empty"
            )
        
        entity_name = await ai_service.extract_entity(description.strip())
        
        return {
            "description": description,
            "extracted_entity": entity_name or "Demo mode: Set up GROQ_API_KEY for AI extraction",
            "confidence": "high" if entity_name else "low"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract entity: {str(e)}"
        )


@router.post("/classify-category")
async def classify_category(request: dict):
    """Classify transaction category using AI - Demo Mode"""
    try:
        description = request.get("description", "")
        amount = request.get("amount", 0.0)
        
        if not description or not description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Description cannot be empty"
            )
        
        category = await ai_service.classify_category(description.strip(), amount)
        
        return {
            "description": description,
            "amount": amount,
            "classified_category": category or "Demo mode: Set up GROQ_API_KEY for AI classification",
            "confidence": "high" if category else "low"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify category: {str(e)}"
        )
