from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any
from .prophet_service import prophet_service
from ..auth.router import get_current_user
from ..models.user import User

router = APIRouter(prefix="/forecasts", tags=["forecasts"])

@router.get("/cashflow")
async def get_cashflow_forecast(
    days: int = Query(30, ge=1, le=365, description="Number of days to forecast"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate cashflow forecast using Prophet"""
    return await prophet_service.generate_cashflow_forecast(current_user.id, days)
