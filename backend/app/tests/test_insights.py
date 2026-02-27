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
        email="test_insights@example.com",
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
async def test_weekly_summary_no_data(test_user):
    """Test weekly summary with no data"""
    response = client.get(
        "/api/v1/insights/weekly-summary",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "no_data"
    assert "message" in data


@pytest.mark.asyncio
async def test_weekly_summary_structure(test_user):
    """Test weekly summary endpoint structure"""
    response = client.get(
        "/api/v1/insights/weekly-summary",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have these fields regardless of data status
    assert "status" in data
    
    if data["status"] == "success":
        assert "period" in data
        assert "financial_data" in data
        assert "ai_summary" in data
        assert "recommendations" in data
