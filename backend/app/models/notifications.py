from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class NotificationPreferences(BaseModel):
    weekly_summary: bool = Field(default=True, description="Receive weekly summary emails")
    alert_emails: bool = Field(default=True, description="Receive alert emails")
    marketing_emails: bool = Field(default=False, description="Receive marketing emails")
    daily_digest: bool = Field(default=False, description="Receive daily digest emails")


class NotificationPreferencesUpdate(BaseModel):
    weekly_summary: Optional[bool] = None
    alert_emails: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    daily_digest: Optional[bool] = None


class EmailTemplate(BaseModel):
    subject: str
    html_content: str
    text_content: Optional[str] = None


class EmailLog(BaseModel):
    id: str
    user_id: str
    email_type: str  # "weekly_summary", "alert", etc.
    recipient: str
    subject: str
    sent_at: str
    status: str  # "sent", "failed"
    error_message: Optional[str] = None
