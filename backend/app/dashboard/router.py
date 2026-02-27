from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime
from ..service import dashboard_service
from ..models.entity import EntitySummary
from ..auth.router import get_current_user
from ..models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/overview")
async def get_overview(current_user: User = Depends(get_current_user)):
    """Get dashboard overview"""
    return await dashboard_service.get_overview(current_user.id)

@router.get("/top-customers")
async def get_top_customers(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get top customers by revenue"""
    return await dashboard_service.get_top_customers(current_user.id, limit)

@router.get("/top-suppliers")
async def get_top_suppliers(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get top suppliers by expenses"""
    return await dashboard_service.get_top_suppliers(current_user.id, limit)

@router.get("/transactions")
async def get_transactions(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    entity_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get transactions with filtering and pagination"""
    return await dashboard_service.get_transactions(
        current_user.id, start_date, end_date, entity_id, page, limit
    )
