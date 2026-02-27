"""Test configuration and fixtures for Iteration 2"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.database import (
    users, transactions, entities, csv_imports, 
    forecasts, alerts, insights_collection
)
from app.models.user import UserCreate


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
async def mock_groq_client():
    """Mock Groq client for AI tests"""
    with patch('app.ai.groq_client.groq_client') as mock:
        # Default mock responses
        mock.extract_entity.return_value = ("Test Entity", 0.8)
        mock.classify_category.return_value = ("Other", 0.5)
        mock.generate_weekly_summary.return_value = {
            "narrative": "Test summary",
            "recommendations": ["Test recommendation"]
        }
        yield mock


@pytest.fixture
async def mock_celery():
    """Mock Celery tasks for testing"""
    with patch('app.tasks.celery_app') as mock:
        mock.Task = Mock
        yield mock


@pytest.fixture
async def test_user_data():
    """Test user data fixture"""
    return UserCreate(
        email="test@example.com",
        password="testpassword123",
        full_name="Test User"
    )


@pytest.fixture
async def authenticated_user(client, test_user_data):
    """Create and authenticate a test user"""
    # Clean up any existing user
    await users.delete_one({"email": test_user_data.email})
    
    # Register user
    response = client.post("/api/v1/auth/register", json=test_user_data.dict())
    assert response.status_code == 200
    
    user_data = response.json()
    token = user_data["access_token"]
    
    return {
        "user": user_data,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


@pytest.fixture
async def sample_csv_data():
    """Sample CSV data for testing"""
    return """Date,Description,Amount,Balance
2024-01-15,AMZN MKTP US,-45.50,15400.00
2024-01-16,Client Payment,1250.00,16650.50
2024-01-17,Office Supplies,-89.99,16560.51
2024-01-18,Software License,-299.00,16261.51
2024-01-19,Restaurant Lunch,-25.00,16236.51"""


@pytest.fixture
async def sample_transactions():
    """Sample transaction data for testing"""
    return [
        {
            "transaction_date": "2024-01-15",
            "description": "AMZN MKTP US",
            "amount": -45.50,
            "entity_id": None,
            "expense_category_id": None
        },
        {
            "transaction_date": "2024-01-16",
            "description": "Client Payment - ABC Corp",
            "amount": 1250.00,
            "entity_id": None,
            "expense_category_id": None
        },
        {
            "transaction_date": "2024-01-17",
            "description": "Office Supplies Store",
            "amount": -89.99,
            "entity_id": None,
            "expense_category_id": None
        }
    ]


@pytest.fixture
async def sample_entities():
    """Sample entity data for testing"""
    return [
        {
            "name": "Amazon",
            "normalized_name": "amazon",
            "entity_type": "supplier",
            "total_revenue": 0.0,
            "total_expense": 500.0,
            "transaction_count": 5
        },
        {
            "name": "ABC Corp",
            "normalized_name": "abc corp",
            "entity_type": "customer",
            "total_revenue": 5000.0,
            "total_expense": 0.0,
            "transaction_count": 3
        }
    ]


@pytest.fixture
async def sample_forecast():
    """Sample forecast data for testing"""
    return {
        "current_balance": 5000.0,
        "forecast": [
            {
                "date": "2024-02-01",
                "projected_balance": 5200.0,
                "projected_revenue": 200.0,
                "projected_expense": 0.0
            },
            {
                "date": "2024-02-02",
                "projected_balance": 5150.0,
                "projected_revenue": 0.0,
                "projected_expense": 50.0
            }
        ],
        "risk_alert": None,
        "confidence": 0.8
    }


@pytest.fixture
async def sample_alerts():
    """Sample alert data for testing"""
    return [
        {
            "alert_type": "anomaly",
            "severity": "medium",
            "title": "Unusual spending detected",
            "message": "Large purchase detected",
            "is_acknowledged": False
        },
        {
            "alert_type": "cashflow_risk",
            "severity": "high",
            "title": "Cashflow risk",
            "message": "Cash may go negative in 15 days",
            "is_acknowledged": False
        }
    ]


# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Clean up test data after each test"""
    yield
    # This runs after each test
    await users.delete_many({"email": {"$regex": r"^test"}})
    await transactions.delete_many({"description": {"$regex": r"^(Test|AMZN|Client|Office|Software|Restaurant)"}})
    await entities.delete_many({"name": {"$regex": r"^(Test|Amazon|ABC)"}})
    await csv_imports.delete_many({"filename": {"$regex": r"^test"}})
    await forecasts.delete_many({})
    await alerts.delete_many({})
    await insights_collection.delete_many({})


# Mock database collections for unit tests
@pytest.fixture
def mock_db_collections():
    """Mock all database collections for unit tests"""
    with patch('app.database.get_transactions_collection') as mock_tx, \
         patch('app.database.get_entities_collection') as mock_entities, \
         patch('app.database.get_imports_collection') as mock_imports, \
         patch('app.database.get_users_collection') as mock_users, \
         patch('app.database.get_forecasts_collection') as mock_forecasts, \
         patch('app.database.get_alerts_collection') as mock_alerts, \
         patch('app.database.get_insights_collection') as mock_insights:
        
        # Setup mock return values
        mock_tx.return_value = Mock()
        mock_entities.return_value = Mock()
        mock_imports.return_value = Mock()
        mock_users.return_value = Mock()
        mock_forecasts.return_value = Mock()
        mock_alerts.return_value = Mock()
        mock_insights.return_value = Mock()
        
        yield {
            "transactions": mock_tx.return_value,
            "entities": mock_entities.return_value,
            "imports": mock_imports.return_value,
            "users": mock_users.return_value,
            "forecasts": mock_forecasts.return_value,
            "alerts": mock_alerts.return_value,
            "insights": mock_insights.return_value
        }


# Performance testing fixtures
@pytest.fixture
async def large_dataset():
    """Create a large dataset for performance testing"""
    transactions = []
    for i in range(1000):
        transactions.append({
            "transaction_date": f"2024-01-{(i % 28) + 1:02d}",
            "description": f"Transaction {i}",
            "amount": -10.0 if i % 2 == 0 else 100.0,
            "entity_id": f"entity_{i % 10}" if i % 5 == 0 else None,
            "expense_category_id": f"cat_{i % 5}" if i % 2 == 0 else None
        })
    return transactions


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, no external deps)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (slower, real DB)"
    )
    config.addinivalue_line(
        "markers", "ai: marks tests that use AI features"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (performance tests)"
    )


# Helper functions for tests
async def create_test_user_with_data(user_data, transactions_data=None):
    """Helper to create user with optional transaction data"""
    # Create user
    user_dict = user_data.dict()
    user_dict.update({
        "_id": f"user_{user_data.email}",
        "is_active": True,
        "created_at": "2024-01-01"
    })
    await users.insert_one(user_dict)
    
    # Create transactions if provided
    if transactions_data:
        for tx in transactions_data:
            tx["user_id"] = user_dict["_id"]
            tx["_id"] = f"tx_{len(transactions_data)}"
        await transactions.insert_many(transactions_data)
    
    return user_dict


def assert_valid_response_structure(response, expected_fields):
    """Helper to validate response structure"""
    assert response.status_code == 200
    data = response.json()
    for field in expected_fields:
        assert field in data, f"Missing field: {field}"
    return data


def mock_task_result(task_id="test_task", status="SUCCESS"):
    """Helper to create mock task results"""
    return Mock(id=task_id, status=status, result={"status": "completed"})
