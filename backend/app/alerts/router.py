from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from .service import alert_service
from ..auth.router import get_current_user
from ..models.user import User

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=List[Dict[str, Any]])
async def get_alerts(current_user: User = Depends(get_current_user)):
    """Get all active alerts"""
    return await alert_service.get_active_alerts(current_user.id)

@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert"""
    success = await alert_service.acknowledge_alert(alert_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found or already processed"
        )
    
    return {"message": "Alert acknowledged successfully"}

@router.put("/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """Dismiss an alert"""
    success = await alert_service.dismiss_alert(alert_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found or already processed"
        )
    
    return {"message": "Alert dismissed successfully"}
