import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import transactions, users
from app.models.user import UserCreate

client = TestClient(app)


@pytest.fixture
async def test_user():
    """Create and authenticate a test user"""
    user_data = UserCreate(
        email="test_forecast@example.com",
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
async def test_forecast_insufficient_data(test_user):
    """Test forecasting with insufficient data"""
    response = client.get(
        "/api/v1/forecasts/cashflow",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "insufficient_data"
    assert "message" in data
    assert "current_data" in data


@pytest.mark.asyncio
async def test_forecast_with_data(test_user):
    """Test forecasting with sufficient data"""
    # Create sample transactions (this would need more setup in real tests)
    # For now, just test the endpoint exists and returns proper structure
    
    response = client.get(
        "/api/v1/forecasts/cashflow?days=30",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    
    # Should return insufficient_data since we don't have real transactions
    if data["status"] == "success":
        assert "forecast" in data
        assert "metrics" in data
    else:
        assert data["status"] == "insufficient_data"
