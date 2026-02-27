"""Test Advanced Dashboard for Iteration 3"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import users, transactions, entities, dashboard_layouts
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
    user_id = response.json()["id"]
    
    return {"user": response.json(), "token": token, "user_id": user_id}


@pytest.fixture
async def sample_transactions(test_user):
    """Create sample transactions for dashboard testing"""
    transactions_data = []
    for i in range(30):  # 30 days of data
        transactions_data.append({
            "_id": f"tx_{i}",
            "user_id": test_user["user_id"],
            "transaction_date": f"2024-01-{(i % 28) + 1:02d}",
            "description": f"Transaction {i}",
            "amount": -10.0 if i % 2 == 0 else 100.0,
            "entity_id": f"entity_{i % 3}" if i % 3 == 0 else None,
            "expense_category_id": f"cat_{i % 5}" if i % 2 == 0 else None
        })
    await transactions.insert_many(transactions_data)
    return transactions_data


# ============= Dashboard Trends Tests =============

@pytest.mark.asyncio
async def test_get_dashboard_trends(test_user, sample_transactions):
    """Test retrieving dashboard trend data"""
    response = client.get(
        "/api/v1/dashboard/trends?period=30d",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "revenue_trend" in data
    assert "expense_trend" in data
    assert "net_income_trend" in data
    assert "period" in data


@pytest.mark.asyncio
async def test_get_cashflow_timeline(test_user, sample_transactions):
    """Test cashflow timeline with historical and projected data"""
    with patch('app.ai.forecasting.generate_cashflow_forecast') as mock_forecast:
        mock_forecast.return_value = {
            "current_balance": 5000.0,
            "forecast": [
                {"date": "2024-02-01", "projected_balance": 5200.0}
            ],
            "risk_alert": None,
            "confidence": 0.8
        }
        
        response = client.get(
            "/api/v1/dashboard/cashflow-timeline?days=60",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "historical" in data
        assert "projected" in data
        assert "current_balance" in data


@pytest.mark.asyncio
async def test_get_dashboard_anomalies(test_user, sample_transactions):
    """Test retrieving anomalies for dashboard"""
    with patch('app.ai.forecasting.detect_anomalies') as mock_detect:
        mock_detect.return_value = [
            {
                "transaction_id": "tx_anomaly",
                "date": "2024-01-15",
                "description": "Large unusual purchase",
                "amount": -500.00,
                "z_score": 3.5,
                "severity": "high"
            }
        ]
        
        response = client.get(
            "/api/v1/dashboard/anomalies?period=30d",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "anomalies" in data
        assert "summary" in data


# ============= Dashboard Layout Tests =============

@pytest.mark.asyncio
async def test_get_dashboard_layout(test_user):
    """Test retrieving saved dashboard layout"""
    response = client.get(
        "/api/v1/dashboard/layout",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "layout" in data
    assert "widgets" in data


@pytest.mark.asyncio
async def test_save_dashboard_layout(test_user):
    """Test saving dashboard layout"""
    layout_data = {
        "layout": {
            "lg": [
                {"i": "overview", "x": 0, "y": 0, "w": 6, "h": 4},
                {"i": "trends", "x": 6, "y": 0, "w": 6, "h": 4}
            ]
        },
        "widgets": [
            {"id": "overview", "type": "kpi", "title": "Overview"},
            {"id": "trends", "type": "chart", "title": "Trends"}
        ]
    }
    
    response = client.put(
        "/api/v1/dashboard/layout",
        json=layout_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "saved" in data
    assert data["saved"] is True


@pytest.mark.asyncio
async def test_reset_dashboard_layout(test_user):
    """Test resetting dashboard to default layout"""
    response = client.post(
        "/api/v1/dashboard/layout/reset",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "layout" in data
    assert "widgets" in data


# ============= Widget Data Tests =============

@pytest.mark.asyncio
async def test_get_widget_data(test_user, sample_transactions):
    """Test retrieving data for specific dashboard widgets"""
    widgets = ["overview", "trends", "cashflow", "anomalies"]
    
    for widget in widgets:
        response = client.get(
            f"/api/v1/dashboard/widgets/{widget}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "widget_id" in data
        assert "data" in data


# ============= Mobile Responsiveness Tests =============

@pytest.mark.asyncio
async def test_mobile_dashboard_layout(test_user):
    """Test mobile-optimized dashboard layout"""
    response = client.get(
        "/api/v1/dashboard/layout?viewport=mobile",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "layout" in data
    assert "viewport" in data
    assert data["viewport"] == "mobile"


# ============= Error Handling Tests =============

@pytest.mark.asyncio
async def test_dashboard_unauthorized():
    """Test dashboard endpoints require authentication"""
    response = client.get("/api/v1/dashboard/trends")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_widget_id(test_user):
    """Test requesting data for non-existent widget"""
    response = client.get(
        "/api/v1/dashboard/widgets/invalid_widget",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


# Cleanup
@pytest.mark.asyncio
async def cleanup_dashboard_test_data():
    """Clean up dashboard test data"""
    await users.delete_many({"email": "test_dashboard@example.com"})
    await transactions.delete_many({"description": {"$regex": r"^Transaction "}})
    await entities.delete_many({"name": {"$regex": r"^(Amazon|ABC|Office)"}})
    await dashboard_layouts.delete_many({})
