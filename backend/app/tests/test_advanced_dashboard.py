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
        email="test_dashboard@example.com",
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
async def test_get_trends(test_user):
    """Test getting trends data"""
    response = client.get(
        "/api/v1/dashboard/trends",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert "daily_data" in data
    assert "weekly_data" in data
    assert "trend_metrics" in data
    assert "data_points" in data


@pytest.mark.asyncio
async def test_get_trends_different_periods(test_user):
    """Test getting trends data for different periods"""
    periods = ["30days", "90days", "1year"]
    
    for period in periods:
        response = client.get(
            f"/api/v1/dashboard/trends?period={period}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == period


@pytest.mark.asyncio
async def test_get_cashflow_timeline(test_user):
    """Test getting cashflow timeline"""
    response = client.get(
        "/api/v1/dashboard/cashflow-timeline",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "historical_days" in data
    assert "forecast_days" in data
    assert "timeline" in data
    assert "forecast_status" in data
    assert "current_balance" in data


@pytest.mark.asyncio
async def test_get_cashflow_timeline_custom_days(test_user):
    """Test getting cashflow timeline with custom days"""
    response = client.get(
        "/api/v1/dashboard/cashflow-timeline?days=60",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["historical_days"] == 60


@pytest.mark.asyncio
async def test_get_anomalies(test_user):
    """Test getting anomalies"""
    response = client.get(
        "/api/v1/dashboard/anomalies",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)  # Should return a list of anomalies


@pytest.mark.asyncio
async def test_get_dashboard_layout(test_user):
    """Test getting dashboard layout"""
    response = client.get(
        "/api/v1/dashboard/layout",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "widgets" in data
    assert "layout" in data
    assert isinstance(data["widgets"], list)


@pytest.mark.asyncio
async def test_save_dashboard_layout(test_user):
    """Test saving dashboard layout"""
    layout_data = {
        "widgets": [
            {
                "id": "custom_widget",
                "type": "custom_type",
                "position": {"x": 0, "y": 0, "w": 6, "h": 4},
                "title": "Custom Widget"
            }
        ],
        "layout": "grid"
    }
    
    response = client.put(
        "/api/v1/dashboard/layout",
        json=layout_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["widgets"][0]["id"] == "custom_widget"
    assert data["layout"] == "grid"


@pytest.mark.asyncio
async def test_dashboard_layout_persistence(test_user):
    """Test that dashboard layout persists"""
    # Save custom layout
    layout_data = {
        "widgets": [
            {
                "id": "persistent_widget",
                "type": "test_type",
                "position": {"x": 1, "y": 1, "w": 4, "h": 3},
                "title": "Persistent Widget"
            }
        ],
        "layout": "grid"
    }
    
    client.put(
        "/api/v1/dashboard/layout",
        json=layout_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Retrieve layout
    response = client.get(
        "/api/v1/dashboard/layout",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["widgets"]) >= 1
    # Should contain our custom widget
    widget_ids = [w["id"] for w in data["widgets"]]
    assert "persistent_widget" in widget_ids
