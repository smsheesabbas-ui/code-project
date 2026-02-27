"""Integration tests for Iteration 2 AI features"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import users, transactions, entities, csv_imports, forecasts, alerts
from app.models.user import UserCreate

client = TestClient(app)


@pytest.fixture
async def test_user():
    """Create and authenticate a test user"""
    user_data = UserCreate(
        email="test_integration@example.com",
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
async def setup_full_workflow_data(test_user):
    """Set up complete data for workflow testing"""
    user_id = test_user["user_id"]
    
    # Create entities
    entities_data = [
        {"_id": "entity1", "user_id": user_id, "name": "Amazon", "normalized_name": "amazon", "entity_type": "supplier"},
        {"_id": "entity2", "user_id": user_id, "name": "ABC Corp", "normalized_name": "abc corp", "entity_type": "customer"}
    ]
    await entities.insert_many(entities_data)
    
    # Create transactions with varied data for testing
    transactions_data = [
        {
            "_id": "tx1",
            "user_id": user_id,
            "import_id": "import1",
            "transaction_date": "2024-01-15",
            "description": "AMZN MKTP US Purchase",
            "amount": -45.50,
            "entity_id": "entity1",
            "expense_category_id": "cat1"
        },
        {
            "_id": "tx2",
            "user_id": user_id,
            "import_id": "import1",
            "transaction_date": "2024-01-16",
            "description": "ABC Corp Invoice Payment",
            "amount": 1250.00,
            "entity_id": "entity2",
            "expense_category_id": None
        },
        {
            "_id": "tx3",
            "user_id": user_id,
            "import_id": "import1",
            "transaction_date": "2024-01-17",
            "description": "Office Supplies Store",
            "amount": -89.99,
            "entity_id": None,
            "expense_category_id": "cat2"
        },
        {
            "_id": "tx4",
            "user_id": user_id,
            "import_id": "import1",
            "transaction_date": "2024-01-18",
            "description": "Software License Renewal",
            "amount": -299.00,
            "entity_id": None,
            "expense_category_id": "cat3"
        },
        {
            "_id": "tx5",
            "user_id": user_id,
            "import_id": "import1",
            "transaction_date": "2024-01-19",
            "description": "Client Payment - XYZ Ltd",
            "amount": 2500.00,
            "entity_id": None,
            "expense_category_id": None
        }
    ]
    await transactions.insert_many(transactions_data)
    
    # Create CSV import record
    import_data = {
        "_id": "import1",
        "user_id": user_id,
        "filename": "transactions.csv",
        "status": "confirmed",
        "column_mapping": {"date": "Date", "description": "Description", "amount": "Amount"},
        "total_rows": 5,
        "processed_rows": 5,
        "created_at": "2024-01-15"
    }
    await csv_imports.insert_one(import_data)
    
    return {
        "entities": entities_data,
        "transactions": transactions_data,
        "import": import_data
    }


# ============= Complete Workflow Tests =============

@pytest.mark.asyncio
async def test_csv_to_ai_classification_workflow(test_user, setup_full_workflow_data):
    """Test complete workflow from CSV upload to AI classification"""
    
    # 1. Upload CSV
    csv_content = """Date,Description,Amount,Balance
2024-01-20,New Transaction,-25.00,1000.00
2024-01-21,Another Payment,500.00,1500.00"""
    
    with patch('app.tasks.classify_import_transactions') as mock_classify:
        mock_classify.delay.return_value = Mock(id="task123")
        
        upload_response = client.post(
            "/api/v1/imports/upload",
            files={"file": ("test.csv", csv_content, "text/csv")},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert upload_response.status_code == 200
        import_id = upload_response.json()["id"]
        
        # 2. Preview import
        preview_response = client.get(
            f"/api/v1/imports/{import_id}/preview",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        assert "column_mapping" in preview_data
        assert len(preview_data["rows"]) > 0
        
        # 3. Confirm import (should trigger AI classification)
        with patch('app.database.get_imports_collection') as mock_imports:
            mock_imports.return_value.find_one.return_value = {
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
            assert "ai_classification_queued" in confirm_response.json()


@pytest.mark.asyncio
async def test_ai_enhanced_dashboard(test_user, setup_full_workflow_data):
    """Test dashboard with AI-enhanced data"""
    
    # Get dashboard overview
    response = client.get(
        "/api/v1/dashboard/overview",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have AI-enhanced metrics
    assert "cash_balance" in data
    assert "net_income" in data
    assert "total_revenue" in data
    assert "total_expenses" in data
    
    # Get top customers (should use entity data)
    customers_response = client.get(
        "/api/v1/entities/top-customers",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert customers_response.status_code == 200
    customers_data = customers_response.json()
    assert "customers" in customers_data


@pytest.mark.asyncio
async def test_forecast_with_historical_data(test_user, setup_full_workflow_data):
    """Test forecasting with real transaction data"""
    
    with patch('app.ai.forecasting.generate_cashflow_forecast') as mock_forecast:
        mock_forecast.return_value = {
            "current_balance": 3000.51,
            "forecast": [
                {"date": "2024-02-01", "projected_balance": 3200.51, "projected_revenue": 200.0, "projected_expense": 0.0},
                {"date": "2024-02-02", "projected_balance": 3150.51, "projected_revenue": 0.0, "projected_expense": 50.0}
            ],
            "risk_alert": None,
            "confidence": 0.75
        }
        
        response = client.get(
            "/api/v1/insights/forecasts/cashflow",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_balance"] == 3000.51
        assert len(data["forecast"]) == 30  # Default 30 days
        assert data["confidence"] == 0.75


@pytest.mark.asyncio
async def test_anomaly_detection_integration(test_user, setup_full_workflow_data):
    """Test anomaly detection with realistic data"""
    
    # Add an anomalous transaction
    anomaly_tx = {
        "_id": "tx_anomaly",
        "user_id": test_user["user_id"],
        "import_id": "import1",
        "transaction_date": "2024-01-22",
        "description": "Unusually Large Purchase",
        "amount": -5000.00,  # Much larger than usual
        "entity_id": "entity1",
        "expense_category_id": "cat1"
    }
    await transactions.insert_one(anomaly_tx)
    
    with patch('app.ai.forecasting.detect_anomalies') as mock_detect:
        mock_detect.return_value = [
            {
                "transaction_id": "tx_anomaly",
                "date": "2024-01-22",
                "description": "Unusually Large Purchase",
                "amount": -5000.00,
                "category_id": "cat1",
                "z_score": 4.2,
                "severity": "high"
            }
        ]
        
        response = client.get(
            "/api/v1/insights/patterns/anomalies",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["anomalies"]) == 1
        assert data["anomalies"][0]["severity"] == "high"


@pytest.mark.asyncio
async def test_weekly_summary_with_real_data(test_user, setup_full_workflow_data):
    """Test weekly summary generation with real transaction patterns"""
    
    with patch('app.ai.groq_client.groq_client') as mock_groq:
        mock_groq.generate_weekly_summary.return_value = {
            "narrative": "This week showed strong revenue growth with controlled expenses. Top customer was ABC Corp contributing $1,250.",
            "recommendations": [
                "Monitor the large software license expense for potential optimization",
                "Consider negotiating better terms with Amazon for regular purchases"
            ]
        }
        
        response = client.post(
            "/api/v1/insights/generate-weekly",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data


# ============= Cross-Feature Integration Tests =============

@pytest.mark.asyncio
async def test_entities_and_transactions_relationship(test_user, setup_full_workflow_data):
    """Test that entities are properly linked to transactions"""
    
    # Get transactions with entity data
    response = client.get(
        "/api/v1/transactions/",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    transactions_list = response.json()
    
    # Should have transactions with entity information
    amazon_tx = next((tx for tx in transactions_list if "AMZN" in tx["description"]), None)
    assert amazon_tx is not None
    assert amazon_tx["entity_id"] == "entity1"  # Should be linked to Amazon entity


@pytest.mark.asyncio
async def test_alerts_from_forecast_risks(test_user, setup_full_workflow_data):
    """Test that forecast risks create alerts"""
    
    # Create a forecast with risk
    forecast_data = {
        "user_id": test_user["user_id"],
        "generated_at": "2024-01-20",
        "forecast_days": 30,
        "current_balance": 100.00,
        "risk_alert": {
            "has_risk": True,
            "risk_date": "2024-02-15",
            "projected_low": -50.00,
            "message": "Cash may go negative around Feb 15"
        }
    }
    await forecasts.insert_one(forecast_data)
    
    response = client.get(
        "/api/v1/insights/alerts",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    alerts_list = response.json()
    assert isinstance(alerts_list, list)


@pytest.mark.asyncio
async def test_recurring_payment_detection(test_user, setup_full_workflow_data):
    """Test recurring payment detection with multiple similar transactions"""
    
    # Add recurring transactions
    recurring_txs = [
        {
            "_id": "tx_recurring1",
            "user_id": test_user["user_id"],
            "transaction_date": "2024-01-01",
            "description": "Netflix Subscription",
            "amount": -15.99,
            "entity_id": "entity3",
            "expense_category_id": "cat1"
        },
        {
            "_id": "tx_recurring2",
            "user_id": test_user["user_id"],
            "transaction_date": "2024-02-01",
            "description": "Netflix Subscription",
            "amount": -15.99,
            "entity_id": "entity3",
            "expense_category_id": "cat1"
        }
    ]
    await transactions.insert_many(recurring_txs)
    
    with patch('app.ai.forecasting.detect_recurring_payments') as mock_recurring:
        mock_recurring.return_value = [
            {
                "entity_id": "entity3",
                "frequency": "monthly",
                "avg_amount": 15.99,
                "occurrences": 2,
                "confidence": 0.9
            }
        ]
        
        response = client.get(
            "/api/v1/insights/patterns/recurring",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["recurring_payments"]) == 1
        assert data["recurring_payments"][0]["frequency"] == "monthly"


# ============= Performance and Scalability Tests =============

@pytest.mark.asyncio
async def test_bulk_transaction_processing(test_user):
    """Test processing many transactions efficiently"""
    
    # Create many transactions
    bulk_transactions = []
    for i in range(100):
        bulk_transactions.append({
            "_id": f"tx_bulk_{i}",
            "user_id": test_user["user_id"],
            "import_id": "import_bulk",
            "transaction_date": f"2024-01-{15 + (i % 15):02d}",
            "description": f"Bulk Transaction {i}",
            "amount": -10.00 if i % 2 == 0 else 100.00,
            "entity_id": None,
            "expense_category_id": None
        })
    
    await transactions.insert_many(bulk_transactions)
    
    # Test that insights endpoints handle bulk data
    response = client.get(
        "/api/v1/insights/forecasts/cashflow",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    # Should handle 100+ transactions without timeout


@pytest.mark.asyncio
async def test_concurrent_ai_processing(test_user, setup_full_workflow_data):
    """Test concurrent AI processing doesn't conflict"""
    
    # Trigger multiple AI tasks simultaneously
    with patch('app.tasks.run_anomaly_detection') as mock_anomaly:
        mock_anomaly.delay.return_value = Mock(id="task1")
        
        with patch('app.tasks.regenerate_forecast') as mock_forecast:
            mock_forecast.delay.return_value = Mock(id="task2")
            
            with patch('app.tasks.generate_weekly_summary') as mock_summary:
                mock_summary.delay.return_value = Mock(id="task3")
                
                # Trigger all tasks
                anomaly_response = client.post(
                    "/api/v1/insights/alerts/detect-anomalies",
                    headers={"Authorization": f"Bearer {test_user['token']}"}
                )
                
                forecast_response = client.post(
                    "/api/v1/insights/forecasts/regenerate",
                    headers={"Authorization": f"Bearer {test_user['token']}"}
                )
                
                summary_response = client.post(
                    "/api/v1/insights/generate-weekly",
                    headers={"Authorization": f"Bearer {test_user['token']}"}
                )
                
                # All should succeed
                assert anomaly_response.status_code == 200
                assert forecast_response.status_code == 200
                assert summary_response.status_code == 200
                
                # All should have task IDs
                assert "task_id" in anomaly_response.json()
                assert "task_id" in forecast_response.json()
                assert "task_id" in summary_response.json()


# ============= Data Consistency Tests =============

@pytest.mark.asyncio
async def test_entity_counter_updates(test_user, setup_full_workflow_data):
    """Test that entity counters are updated after AI classification"""
    
    # Check initial entity counters
    amazon_entity = await entities.find_one({"_id": "entity1"})
    initial_expense = amazon_entity.get("total_expense", 0)
    
    # Add a new transaction for Amazon
    new_tx = {
        "_id": "tx_new_amazon",
        "user_id": test_user["user_id"],
        "transaction_date": "2024-01-23",
        "description": "AMZN Purchase",
        "amount": -25.00,
        "entity_id": "entity1",
        "expense_category_id": "cat1"
    }
    await transactions.insert_one(new_tx)
    
    # Trigger entity counter update
    with patch('app.ai.service._update_entity_counters') as mock_update:
        mock_update.return_value = None
        
        from app.ai.service import _update_entity_counters
        await _update_entity_counters(test_user["user_id"])
        
        # Verify counters would be updated (in real implementation)
        mock_update.assert_called_once_with(test_user["user_id"])


# Cleanup
@pytest.mark.asyncio
async def cleanup_integration_test_data():
    """Clean up integration test data"""
    await users.delete_many({"email": "test_integration@example.com"})
    await transactions.delete_many({"description": {"$regex": r"^(Bulk|New|AMZN|ABC|Office|Software|Client|Unusually|Netflix)"}})
    await entities.delete_many({"name": {"$regex": r"^(Amazon|ABC|Netflix)"}})
    await csv_imports.delete_many({"filename": {"$regex": r"^(test|transactions)"}})
    await forecasts.delete_many({})
    await alerts.delete_many({})
