from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
from .service import notification_service
from ..models.notifications import NotificationPreferences, NotificationPreferencesUpdate
from ..auth.router import get_current_user
from ..models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(current_user: User = Depends(get_current_user)):
    """Get user's notification preferences"""
    return await notification_service.get_notification_preferences(current_user.id)

@router.put("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    update_data: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user's notification preferences"""
    return await notification_service.update_notification_preferences(current_user.id, update_data)

@router.post("/send-weekly-summary")
async def send_weekly_summary(current_user: User = Depends(get_current_user)):
    """Send weekly summary email to current user"""
    success = await notification_service.send_weekly_summary_to_user(current_user.id)
    
    if success:
        return {"message": "Weekly summary sent successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send weekly summary"
        )

@router.get("/stats")
async def get_email_stats(current_user: User = Depends(get_current_user)):
    """Get email statistics for current user"""
    return await notification_service.get_email_stats(current_user.id)
