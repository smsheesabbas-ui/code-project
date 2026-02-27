import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from ..config import settings
from ..database import users
from ..insights.service import insights_service
from ..alerts.service import alert_service
import resend


class EmailService:
    def __init__(self):
        if not settings.RESEND_API_KEY:
            print("Warning: RESEND_API_KEY not configured. Email features will be disabled.")
            self.enabled = False
        else:
            resend.api_key = settings.RESEND_API_KEY
            self.enabled = True
    
    async def send_weekly_summary(self, user_id: str) -> bool:
        """Send weekly summary email to user"""
        if not self.enabled:
            return False
        
        try:
            # Get user data
            user = await users.find_one({"id": user_id, "is_active": True})
            if not user or not user.get("email"):
                return False
            
            # Check notification preferences
            prefs = user.get("notification_preferences", {})
            if not prefs.get("weekly_summary", False):
                return False
            
            # Get weekly summary data
            summary_data = await insights_service.get_weekly_summary(user_id)
            
            # Generate HTML email
            html_content = self._generate_weekly_summary_html(summary_data, user)
            
            # Send email
            params = {
                "from": settings.EMAIL_FROM,
                "to": [user["email"]],
                "subject": f"Your Weekly Financial Summary - {datetime.now().strftime('%B %d, %Y')}",
                "html": html_content
            }
            
            result = resend.Emails.send(params)
            
            print(f"Weekly summary sent to {user['email']}: {result['id']}")
            return True
            
        except Exception as e:
            print(f"Error sending weekly summary to user {user_id}: {e}")
            return False
    
    async def send_alert_email(self, user_id: str, alert_data: Dict[str, Any]) -> bool:
        """Send alert email to user"""
        if not self.enabled:
            return False
        
        try:
            # Get user data
            user = await users.find_one({"id": user_id, "is_active": True})
            if not user or not user.get("email"):
                return False
            
            # Check notification preferences
            prefs = user.get("notification_preferences", {})
            if not prefs.get("alert_emails", False):
                return False
            
            # Generate HTML email
            html_content = self._generate_alert_html(alert_data, user)
            
            # Send email
            params = {
                "from": settings.EMAIL_FROM,
                "to": [user["email"]],
                "subject": f"Alert: {alert_data['title']}",
                "html": html_content
            }
            
            result = resend.Emails.send(params)
            
            print(f"Alert email sent to {user['email']}: {result['id']}")
            return True
            
        except Exception as e:
            print(f"Error sending alert email to user {user_id}: {e}")
            return False
    
    def _generate_weekly_summary_html(self, summary_data: Dict[str, Any], user: Dict[str, Any]) -> str:
        """Generate HTML for weekly summary email"""
        
        if summary_data.get("status") == "no_data":
            return self._generate_no_data_email(user)
        
        financial_data = summary_data.get("financial_data", {})
        ai_summary = summary_data.get("ai_summary", "")
        recommendations = summary_data.get("recommendations", [])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly Financial Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4f46e5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .metric {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 15px; background: white; border-radius: 6px; }}
                .metric-value {{ font-weight: bold; color: #4f46e5; }}
                .summary {{ margin: 20px 0; padding: 20px; background: white; border-left: 4px solid #4f46e5; border-radius: 4px; }}
                .recommendations {{ margin: 20px 0; }}
                .recommendation {{ margin: 10px 0; padding: 10px; background: #e0e7ff; border-radius: 4px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Weekly Financial Summary</h1>
                    <p>{user.get('full_name', 'Valued Customer')}</p>
                </div>
                <div class="content">
                    <h2>Your Week at a Glance</h2>
                    
                    <div class="metric">
                        <span>Total Revenue</span>
                        <span class="metric-value">${financial_data.get('total_revenue', 0):,.2f}</span>
                    </div>
                    
                    <div class="metric">
                        <span>Total Expenses</span>
                        <span class="metric-value">${financial_data.get('total_expenses', 0):,.2f}</span>
                    </div>
                    
                    <div class="metric">
                        <span>Net Income</span>
                        <span class="metric-value">${financial_data.get('net_income', 0):,.2f}</span>
                    </div>
                    
                    <div class="metric">
                        <span>Transactions</span>
                        <span class="metric-value">{financial_data.get('transaction_count', 0)}</span>
                    </div>
                    
                    <div class="summary">
                        <h3>AI Summary</h3>
                        <p>{ai_summary}</p>
                    </div>
                    
                    {self._generate_recommendations_html(recommendations)}
                    
                    <div class="footer">
                        <p>This is your automated weekly financial summary from CashFlow AI.</p>
                        <p>Log in to your dashboard for more detailed insights.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """Generate HTML for recommendations section"""
        if not recommendations:
            return ""
        
        html = '<div class="recommendations"><h3>Recommendations</h3>'
        
        for i, rec in enumerate(recommendations, 1):
            html += f'<div class="recommendation">{i}. {rec}</div>'
        
        html += '</div>'
        return html
    
    def _generate_alert_html(self, alert_data: Dict[str, Any], user: Dict[str, Any]) -> str:
        """Generate HTML for alert email"""
        
        severity_colors = {
            "high": "#dc2626",
            "medium": "#f59e0b", 
            "low": "#10b981"
        }
        
        severity = alert_data.get("severity", "medium")
        color = severity_colors.get(severity, "#f59e0b")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Financial Alert</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {color}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .alert-box {{ background: white; border-left: 4px solid {color}; padding: 20px; margin: 20px 0; border-radius: 4px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Financial Alert</h1>
                    <p>{alert_data.get('title', 'Alert')}</p>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <h3>{alert_data.get('title', 'Alert')}</h3>
                        <p>{alert_data.get('message', 'Please check your dashboard for more information.')}</p>
                    </div>
                    
                    <div class="footer">
                        <p>This alert was generated automatically by CashFlow AI.</p>
                        <p>Log in to your dashboard to take action.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_no_data_email(self, user: Dict[str, Any]) -> str:
        """Generate HTML for no data email"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly Financial Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4f46e5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .message {{ text-align: center; padding: 40px; background: white; border-radius: 6px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Weekly Financial Summary</h1>
                    <p>{user.get('full_name', 'Valued Customer')}</p>
                </div>
                <div class="content">
                    <div class="message">
                        <h3>No Financial Activity This Week</h3>
                        <p>We didn't detect any transactions in your account this week.</p>
                        <p>Upload your bank statements to get detailed insights and summaries.</p>
                    </div>
                    
                    <div class="footer">
                        <p>This is your automated weekly financial summary from CashFlow AI.</p>
                        <p>Log in to your dashboard to upload transactions.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html


email_service = EmailService()
