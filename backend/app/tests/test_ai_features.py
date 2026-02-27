"""Test AI features for Iteration 2"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.database import users, transactions, entities
from app.models.user import UserCreate

client = TestClient(app)


@pytest.fixture
async def test_user():
    """Create and authenticate a test user"""
    user_data = UserCreate(
        email="test_ai@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    
    # Clean up any existing user
    await users.delete_one({"email": user_data.email})
    
    # Register user
    response = client.post("/api/v1/auth/register", json=user_data.dict())
    token = response.json()["access_token"]
    
    return {"user": response.json(), "token": token}


@pytest.fixture
async def sample_transactions(test_user):
    """Create sample transactions for testing"""
    transactions_data = [
        {
            "user_id": test_user["user"]["id"],
            "transaction_date": "2024-01-15",
            "description": "AMZN MKTP US",
            "amount": -45.50,
            "entity_id": None,
            "expense_category_id": None
        },
        {
            "user_id": test_user["user"]["id"],
            "transaction_date": "2024-01-16",
            "description": "Client Payment - ABC Corp",
            "amount": 1250.00,
            "entity_id": None,
            "expense_category_id": None
        },
        {
            "user_id": test_user["user"]["id"],
            "transaction_date": "2024-01-17",
            "description": "Office Supplies Store",
            "amount": -89.99,
            "entity_id": None,
            "expense_category_id": None
        }
    ]
    
    # Insert transactions
    result = await transactions.insert_many(transactions_data)
    return str(result.inserted_ids[0])


# ============= AI Entity Extraction Tests =============

@pytest.mark.asyncio
async def test_entity_extraction_amazon(test_user):
    """Test AI extracts 'Amazon' from 'AMZN MKTP US'"""
    with patch('app.ai.groq_client.groq_client') as mock_groq:
        mock_groq.extract_entity.return_value = ("Amazon", 0.9)
        
        response = client.post(
            "/api/v1/ai/extract-entity",
            json={"description": "AMZN MKTP US"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["entity"] == "Amazon"
        assert data["confidence"] == 0.9


@pytest.mark.asyncio
async def test_entity_extraction_unknown(test_user):
    """Test AI returns 'Unknown' for unclear descriptions"""
    with patch('app.ai.groq_client.groq_client') as mock_groq:
        mock_groq.extract_entity.return_value = ("Unknown", 0.1)
        
        response = client.post(
            "/api/v1/ai/extract-entity",
            json={"description": "Random transaction"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["entity"] == "Unknown"
        assert data["confidence"] == 0.1


# ============= AI Categorization Tests =============

@pytest.mark.asyncio
async def test_expense_categorization_software(test_user):
    """Test AI categorizes software subscription"""
    with patch('app.ai.groq_client.groq_client') as mock_groq:
        mock_groq.classify_category.return_value = ("Software & Subscriptions", 0.85)
        
        response = client.post(
            "/api/v1/ai/categorize-transaction",
            json={
                "description": "Adobe Creative Cloud",
                "amount": -29.99
            },
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Software & Subscriptions"
        assert data["confidence"] == 0.85


@pytest.mark.asyncio
async def test_expense_categorization_meals(test_user):
    """Test AI categorizes meal expense"""
    with patch('app.ai.groq_client.groq_client') as mock_groq:
        mock_groq.classify_category.return_value = ("Meals & Entertainment", 0.8)
        
        response = client.post(
            "/api/v1/ai/categorize-transaction",
            json={
                "description": "Restaurant lunch",
                "amount": -25.00
            },
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Meals & Entertainment"
        assert data["confidence"] == 0.8


# ============= Batch Classification Tests =============

@pytest.mark.asyncio
async def test_batch_classification(test_user, sample_transactions):
    """Test batch classification of transactions"""
    with patch('app.ai.service.classify_transaction') as mock_classify:
        mock_classify.return_value = {
            "transaction_id": sample_transactions,
            "entity_id": "entity123",
            "category_id": "category123",
            "classified": True
        }
        
        response = client.post(
            "/api/v1/ai/classify-batch",
            json={"transaction_ids": [sample_transactions]},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "processed" in data
        assert "classified" in data


# ============= Forecasting Tests =============

@pytest.mark.asyncio
async def test_cashflow_forecast_insufficient_data(test_user):
    """Test forecasting with insufficient data"""
    response = client.get(
        "/api/v1/insights/forecasts/cashflow",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "current_balance" in data
    assert "forecast" in data
    assert len(data["forecast"]) == 30  # Default 30 days


@pytest.mark.asyncio
async def test_cashflow_forecast_with_data(test_user, sample_transactions):
    """Test forecasting with some transaction data"""
    response = client.get(
        "/api/v1/insights/forecasts/cashflow?days=60",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["forecast"]) == 60
    assert all("date" in f for f in data["forecast"])
    assert all("projected_balance" in f for f in data["forecast"])


# ============= Anomaly Detection Tests =============

@pytest.mark.asyncio
async def test_anomaly_detection(test_user):
    """Test anomaly detection endpoint"""
    response = client.get(
        "/api/v1/insights/patterns/anomalies",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data
    assert isinstance(data["anomalies"], list)


# ============= Weekly Summary Tests =============

@pytest.mark.asyncio
async def test_weekly_summary_generation(test_user):
    """Test weekly AI summary generation"""
    with patch('app.ai.groq_client.groq_client') as mock_groq:
        mock_groq.generate_weekly_summary.return_value = {
            "narrative": "This week you spent $135.49 on expenses and earned $1,250 in revenue.",
            "recommendations": ["Consider reducing software subscriptions", "Follow up on late payments"]
        }
        
        response = client.post(
            "/api/v1/insights/generate-weekly",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data


@pytest.mark.asyncio
async def test_weekly_summary_retrieval(test_user):
    """Test retrieving weekly summary"""
    response = client.get(
        "/api/v1/insights/weekly-summary",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data or "period" in data  # Either no data or summary exists


# ============= Alert System Tests =============

@pytest.mark.asyncio
async def test_alerts_listing(test_user):
    """Test listing user alerts"""
    response = client.get(
        "/api/v1/insights/alerts",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_alert_acknowledgment(test_user):
    """Test acknowledging an alert"""
    # First create an alert (would need setup in real test)
    # For now, test with non-existent alert
    response = client.put(
        "/api/v1/insights/alerts/non-existent-id/acknowledge",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


# ============= Background Job Tests =============

@pytest.mark.asyncio
async def test_trigger_anomaly_detection_job(test_user):
    """Test triggering anomaly detection background job"""
    with patch('app.tasks.run_anomaly_detection') as mock_task:
        mock_task.delay.return_value = Mock(id="task123")
        
        response = client.post(
            "/api/v1/insights/alerts/detect-anomalies",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["task_id"] == "task123"


@pytest.mark.asyncio
async def test_trigger_forecast_regeneration(test_user):
    """Test triggering forecast regeneration background job"""
    with patch('app.tasks.regenerate_forecast') as mock_task:
        mock_task.delay.return_value = Mock(id="task456")
        
        response = client.post(
            "/api/v1/insights/forecasts/regenerate",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["task_id"] == "task456"


# ============= Integration Tests =============

@pytest.mark.asyncio
async def test_ai_classification_after_import(test_user):
    """Test that AI classification is triggered after CSV import confirmation"""
    with patch('app.tasks.classify_import_transactions') as mock_task:
        mock_task.delay.return_value = Mock(id="task789")
        
        # Create a mock CSV import
        csv_content = "Date,Description,Amount\n2024-01-15,Test Transaction,-50.00"
        
        response = client.post(
            "/api/v1/imports/upload",
            files={"file": ("test.csv", csv_content, "text/csv")},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        import_id = response.json()["id"]
        
        # Confirm import (should trigger AI classification)
        with patch('app.database.get_imports_collection') as mock_collection:
            mock_collection.return_value.find_one.return_value = {
                "_id": import_id,
                "status": "preview_ready",
                "column_mapping": {"date": "Date", "description": "Description", "amount": "Amount"}
            }
            
            confirm_response = client.post(
                f"/api/v1/imports/{import_id}/confirm",
                json={"duplicate_action": "skip"},
                headers={"Authorization": f"Bearer {test_user['token']}"}
            )
            
            assert confirm_response.status_code == 200
            # AI classification should be queued
            mock_task.delay.assert_called_once()


# ============= Error Handling Tests =============

@pytest.mark.asyncio
async def test_ai_service_error_handling(test_user):
    """Test AI service error handling"""
    with patch('app.ai.groq_client.groq_client') as mock_groq:
        mock_groq.extract_entity.side_effect = Exception("API Error")
        
        response = client.post(
            "/api/v1/ai/extract-entity",
            json={"description": "Test"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        # Should handle error gracefully
        assert response.status_code in [500, 200]
        if response.status_code == 200:
            data = response.json()
            assert data["entity"] == "Unknown"  # Fallback value


@pytest.mark.asyncio
async def test_ai_endpoint_unauthorized():
    """Test AI endpoints require authentication"""
    response = client.post(
        "/api/v1/ai/extract-entity",
        json={"description": "Test"}
    )
    
    assert response.status_code == 401


# Cleanup
@pytest.mark.asyncio
async def cleanup_ai_test_data():
    """Clean up AI test data"""
    await users.delete_many({"email": {"$regex": r"^test_ai"}})
    await transactions.delete_many({"description": {"$regex": r"^(Test|AMZN|Client|Office)"}})
    await entities.delete_many({"name": {"$regex": r"^(Test|Amazon)"}})
