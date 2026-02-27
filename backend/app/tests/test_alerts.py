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
        email="test_alerts@example.com",
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
async def test_get_alerts(test_user):
    """Test getting alerts"""
    response = client.get(
        "/api/v1/alerts/",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_acknowledge_alert(test_user):
    """Test acknowledging an alert"""
    # First create an alert (this would need setup in real tests)
    # For now, test with a non-existent alert ID
    
    response = client.put(
        "/api/v1/alerts/non-existent-id/acknowledge",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Should return 404 for non-existent alert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dismiss_alert(test_user):
    """Test dismissing an alert"""
    response = client.put(
        "/api/v1/alerts/non-existent-id/dismiss",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Should return 404 for non-existent alert
    assert response.status_code == 404
