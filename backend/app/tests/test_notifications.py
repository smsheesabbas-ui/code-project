import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import users
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
    
    return {"user": response.json(), "token": token}


@pytest.mark.asyncio
async def test_get_notification_preferences(test_user):
    """Test getting notification preferences"""
    response = client.get(
        "/api/v1/notifications/preferences",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "weekly_summary" in data
    assert "alert_emails" in data
    assert "marketing_emails" in data
    assert "daily_digest" in data


@pytest.mark.asyncio
async def test_update_notification_preferences(test_user):
    """Test updating notification preferences"""
    update_data = {
        "weekly_summary": False,
        "marketing_emails": True
    }
    
    response = client.put(
        "/api/v1/notifications/preferences",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["weekly_summary"] == False
    assert data["marketing_emails"] == True
    assert data["alert_emails"] == True  # Should remain unchanged


@pytest.mark.asyncio
async def test_send_weekly_summary(test_user):
    """Test sending weekly summary (will fail without Resend API key)"""
    response = client.post(
        "/api/v1/notifications/send-weekly-summary",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Should fail without proper Resend API key configuration
    assert response.status_code in [200, 500]
    
    if response.status_code == 500:
        assert "Failed to send weekly summary" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_email_stats(test_user):
    """Test getting email statistics"""
    response = client.get(
        "/api/v1/notifications/stats",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "preferences" in data
    assert "weekly_summary_enabled" in data
    assert "alert_emails_enabled" in data
