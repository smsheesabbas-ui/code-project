from fastapi import APIRouter, Depends
from typing import Dict, Any
from .service import insights_service
from ..auth.router import get_current_user
from ..models.user import User

router = APIRouter(prefix="/insights", tags=["insights"])

@router.get("/weekly-summary")
async def get_weekly_summary(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Get AI-powered weekly financial summary"""
    return await insights_service.get_weekly_summary(current_user.id)
