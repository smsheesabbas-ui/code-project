"""Test Email Notifications for Iteration 3"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import users, notification_preferences, alerts
from app.models.user import UserCreate

client = TestClient(app)


@pytest.fixture
async def test_user():
    """Create and authenticate a test user"""
    user_data = UserCreate(
        email="test_notifications@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    
    # Clean up any existing user
    await users.delete_one({"email": user_data.email})
    
    # Register user
    response = client.post("/api/v1/auth/register", json=user_data.dict())
    token = response.json()["access_token"]
    user_id = response.json()["id"]
    
    return {"user": response.json(), "token": token, "user_id": user_id}


@pytest.fixture
async def sample_alerts(test_user):
    """Create sample alerts for notification testing"""
    alerts_data = [
        {
            "_id": "alert1",
            "user_id": test_user["user_id"],
            "alert_type": "anomaly",
            "severity": "medium",
            "title": "Unusual Spending Detected",
            "message": "Large purchase of $500.00 detected at Amazon",
            "is_acknowledged": False,
            "created_at": "2024-01-20"
        },
        {
            "_id": "alert2",
            "user_id": test_user["user_id"],
            "alert_type": "cashflow_risk",
            "severity": "high",
            "title": "Cashflow Risk",
            "message": "Cash may go negative in 15 days based on current trends",
            "is_acknowledged": False,
            "created_at": "2024-01-21"
        }
    ]
    await alerts.insert_many(alerts_data)
    return alerts_data


# ============= Notification Preferences Tests =============

@pytest.mark.asyncio
async def test_get_notification_preferences(test_user):
    """Test retrieving user notification preferences"""
    response = client.get(
        "/api/v1/notifications/preferences",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "email_enabled" in data
    assert "weekly_summary" in data
    assert "alert_emails" in data
    assert "email_address" in data


@pytest.mark.asyncio
async def test_update_notification_preferences(test_user):
    """Test updating notification preferences"""
    preferences = {
        "email_enabled": True,
        "weekly_summary": True,
        "alert_emails": True,
        "email_address": "updated@example.com"
    }
    
    response = client.put(
        "/api/v1/notifications/preferences",
        json=preferences,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email_enabled"] == True
    assert data["weekly_summary"] == True
    assert data["email_address"] == "updated@example.com"


@pytest.mark.asyncio
async def test_send_weekly_summary_email(test_user, sample_alerts):
    """Test sending weekly summary email"""
    with patch('app.notifications.email_service.resend') as mock_resend:
        mock_resend.Emails.send.return_value = {"id": "email123"}
        
        response = client.post(
            "/api/v1/notifications/send-weekly-summary",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "email_id" in data
        assert data["status"] == "sent"
        
        # Verify email was sent
        mock_resend.Emails.send.assert_called_once()


@pytest.mark.asyncio
async def test_send_alert_email(test_user, sample_alerts):
    """Test sending alert email"""
    with patch('app.notifications.email_service.resend') as mock_resend:
        mock_resend.Emails.send.return_value = {"id": "alert_email123"}
        
        response = client.post(
            f"/api/v1/notifications/send-alert/{sample_alerts[0]['_id']}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "email_id" in data
        assert data["status"] == "sent"


@pytest.mark.asyncio
async def test_weekly_summary_scheduled_task(test_user):
    """Test weekly summary scheduled task"""
    with patch('app.tasks.send_weekly_summaries') as mock_task:
        mock_task.return_value = {"sent": 5, "skipped": 2}
        
        response = client.post(
            "/api/v1/notifications/trigger-weekly-summary",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data


# ============= Email Template Tests =============

@pytest.mark.asyncio
async def test_weekly_summary_email_template(test_user, sample_alerts):
    """Test weekly summary email template generation"""
    with patch('app.notifications.email_service.render_weekly_summary_template') as mock_template:
        mock_template.return_value = "<html><body><h1>Weekly Summary</h1></body></html>"
        
        with patch('app.notifications.email_service.resend') as mock_resend:
            mock_resend.Emails.send.return_value = {"id": "email123"}
            
            response = client.post(
                "/api/v1/notifications/send-weekly-summary",
                headers={"Authorization": f"Bearer {test_user['token']}"}
            )
            
            assert response.status_code == 200
            mock_template.assert_called_once()


@pytest.mark.asyncio
async def test_resend_api_integration(test_user):
    """Test Resend.com API integration"""
    with patch('app.notifications.email_service.resend') as mock_resend:
        mock_resend.Emails.send.return_value = {
            "id": "resend_email_123",
            "from": "alerts@cashflow.ai",
            "to": test_user["user"]["email"]
        }
        
        response = client.post(
            "/api/v1/notifications/test-email",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "email_id" in data


# ============= Error Handling Tests =============

@pytest.mark.asyncio
async def test_notification_unauthorized():
    """Test notification endpoints require authentication"""
    response = client.get("/api/v1/notifications/preferences")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_alert_notification(test_user):
    """Test sending notification for non-existent alert"""
    response = client.post(
        "/api/v1/notifications/send-alert/non-existent-id",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_resend_api_error_handling(test_user):
    """Test Resend.com API error handling"""
    with patch('app.notifications.email_service.resend') as mock_resend:
        mock_resend.Emails.send.side_effect = Exception("API Error: Invalid API key")
        
        response = client.post(
            "/api/v1/notifications/test-email",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


# Cleanup
@pytest.mark.asyncio
async def cleanup_notification_test_data():
    """Clean up notification test data"""
    await users.delete_many({"email": "test_notifications@example.com"})
    await notification_preferences.delete_many({})
    await alerts.delete_many({"title": {"$regex": r"^(Unusual|Cashflow)"}})
