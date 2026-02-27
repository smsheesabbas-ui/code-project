from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any
from .advanced_service import advanced_dashboard_service
from ..auth.router import get_current_user
from ..models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/trends")
async def get_trends(
    period: str = Query("90days", description="Period: 30days, 90days, 1year"),
    current_user: User = Depends(get_current_user)
):
    """Get trends data for dashboard charts"""
    return await advanced_dashboard_service.get_trends_data(current_user.id, period)

@router.get("/cashflow-timeline")
async def get_cashflow_timeline(
    days: int = Query(90, ge=30, le=365, description="Historical days to include"),
    current_user: User = Depends(get_current_user)
):
    """Get cashflow timeline with historical and projected data"""
    return await advanced_dashboard_service.get_cashflow_timeline(current_user.id, days)

@router.get("/anomalies")
async def get_anomalies(
    period: str = Query("90days", description="Period: 30days, 90days"),
    current_user: User = Depends(get_current_user)
):
    """Get recent anomalies in financial data"""
    return await advanced_dashboard_service.get_anomalies(current_user.id, period)

@router.get("/layout")
async def get_dashboard_layout(current_user: User = Depends(get_current_user)):
    """Get user's dashboard layout"""
    return await advanced_dashboard_service.get_dashboard_layout(current_user.id)

@router.put("/layout")
async def save_dashboard_layout(
    layout: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Save user's dashboard layout"""
    return await advanced_dashboard_service.save_dashboard_layout(current_user.id, layout)
