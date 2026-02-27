from typing import Dict, Any, Optional
from ..database import users
from ..models.notifications import NotificationPreferences, NotificationPreferencesUpdate
from .email_service import email_service


class NotificationService:
    def __init__(self):
        self.email_service = email_service
    
    async def get_notification_preferences(self, user_id: str) -> NotificationPreferences:
        """Get user's notification preferences"""
        user = await users.find_one({"id": user_id})
        if not user:
            raise ValueError("User not found")
        
        prefs_data = user.get("notification_preferences", {})
        
        # Merge with defaults
        default_prefs = NotificationPreferences()
        prefs = NotificationPreferences(
            weekly_summary=prefs_data.get("weekly_summary", default_prefs.weekly_summary),
            alert_emails=prefs_data.get("alert_emails", default_prefs.alert_emails),
            marketing_emails=prefs_data.get("marketing_emails", default_prefs.marketing_emails),
            daily_digest=prefs_data.get("daily_digest", default_prefs.daily_digest)
        )
        
        return prefs
    
    async def update_notification_preferences(
        self, 
        user_id: str, 
        update_data: NotificationPreferencesUpdate
    ) -> NotificationPreferences:
        """Update user's notification preferences"""
        
        # Get current preferences
        current_prefs = await self.get_notification_preferences(user_id)
        
        # Update with new values
        update_dict = update_data.dict(exclude_unset=True)
        
        if not update_dict:
            return current_prefs
        
        # Create updated preferences
        updated_prefs_dict = current_prefs.dict()
        updated_prefs_dict.update(update_dict)
        
        # Save to database
        await users.update_one(
            {"id": user_id},
            {"$set": {"notification_preferences": updated_prefs_dict}}
        )
        
        # Return updated preferences
        return NotificationPreferences(**updated_prefs_dict)
    
    async def send_weekly_summary_to_user(self, user_id: str) -> bool:
        """Send weekly summary to specific user"""
        return await self.email_service.send_weekly_summary(user_id)
    
    async def send_alert_to_user(self, user_id: str, alert_data: Dict[str, Any]) -> bool:
        """Send alert to specific user"""
        return await self.email_service.send_alert_email(user_id, alert_data)
    
    async def send_weekly_summaries_to_all_users(self) -> Dict[str, Any]:
        """Send weekly summaries to all users with preferences enabled"""
        
        # Get all active users with weekly summary enabled
        cursor = users.find({
            "is_active": True,
            "notification_preferences.weekly_summary": True
        })
        
        sent_count = 0
        failed_count = 0
        
        async for user in cursor:
            try:
                success = await self.send_weekly_summary_to_user(user["id"])
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"Failed to send weekly summary to user {user['id']}: {e}")
                failed_count += 1
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "total": sent_count + failed_count
        }
    
    async def get_email_stats(self, user_id: str) -> Dict[str, Any]:
        """Get email statistics for a user"""
        # This would require an email logs collection
        # For now, return basic info
        prefs = await self.get_notification_preferences(user_id)
        
        return {
            "user_id": user_id,
            "preferences": prefs.dict(),
            "weekly_summary_enabled": prefs.weekly_summary,
            "alert_emails_enabled": prefs.alert_emails
        }


notification_service = NotificationService()
