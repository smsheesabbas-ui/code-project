"""Test Celery background tasks for Iteration 2"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.tasks import (
    process_csv_import, classify_import_transactions, regenerate_forecast,
    run_anomaly_detection, generate_weekly_summary
)
from app.database import csv_imports, transactions, entities, users
from app.models.user import UserCreate


@pytest.fixture
async def test_user():
    """Create a test user for task testing"""
    user_data = UserCreate(
        email="test_tasks@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    
    # Clean up any existing user
    await users.delete_one({"email": user_data.email})
    
    # Register user
    user_dict = user_data.dict()
    user_dict.update({
        "_id": "user123",
        "is_active": True,
        "created_at": "2024-01-01"
    })
    await users.insert_one(user_dict)
    
    return user_dict


@pytest.fixture
async def sample_import():
    """Create a sample CSV import record"""
    import_data = {
        "_id": "import123",
        "user_id": "user123",
        "filename": "test.csv",
        "status": "preview_ready",
        "column_mapping": {
            "date": "Date",
            "description": "Description",
            "amount": "Amount"
        },
        "total_rows": 10,
        "processed_rows": 0,
        "created_at": "2024-01-01"
    }
    await csv_imports.insert_one(import_data)
    return import_data


@pytest.fixture
async def sample_transactions():
    """Create sample transactions for testing"""
    transactions_data = [
        {
            "_id": "tx1",
            "user_id": "user123",
            "import_id": "import123",
            "transaction_date": "2024-01-15",
            "description": "AMZN MKTP US",
            "amount": -45.50,
            "entity_id": None,
            "expense_category_id": None
        },
        {
            "_id": "tx2",
            "user_id": "user123",
            "import_id": "import123",
            "transaction_date": "2024-01-16",
            "description": "Client Payment",
            "amount": 1250.00,
            "entity_id": None,
            "expense_category_id": None
        }
    ]
    await transactions.insert_many(transactions_data)
    return transactions_data


# ============= CSV Import Task Tests =============

@pytest.mark.asyncio
async def test_process_csv_import_task_success(test_user, sample_import):
    """Test CSV import background task success"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.tasks.csv_imports') as mock_collection:
        mock_collection.find_one.return_value = sample_import
        mock_collection.update_one.return_value = Mock()
        
        with patch('app.tasks.ingestion_service') as mock_service:
            mock_service.process_csv = AsyncMock(return_value=sample_import)
            
            with patch('app.tasks.classify_transactions') as mock_classify:
                mock_classify.delay.return_value = Mock()
                
                result = process_csv_import(mock_task, "import123", "user123")
                
                assert result["status"] == "completed"
                assert result["import_id"] == "import123"
                mock_classify.delay.assert_called_once_with("import123", "user123")


@pytest.mark.asyncio
async def test_process_csv_import_task_not_found(test_user):
    """Test CSV import task with non-existent import"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.tasks.csv_imports') as mock_collection:
        mock_collection.find_one.return_value = None
        
        with pytest.raises(ValueError, match="import123 not found"):
            process_csv_import(mock_task, "import123", "user123")


# ============= AI Classification Task Tests =============

@pytest.mark.asyncio
async def test_classify_import_transactions_task(test_user, sample_transactions):
    """Test AI classification background task"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.ai.service.classify_transactions_batch') as mock_classify:
        mock_classify.return_value = {
            "import_id": "import123",
            "total_processed": 2,
            "classified": 2
        }
        
        result = classify_import_transactions(mock_task, "import123", "user123")
        
        assert result["import_id"] == "import123"
        assert result["classified"] == 2
        assert result["total"] == 2


@pytest.mark.asyncio
async def test_classify_import_transactions_progress(test_user, sample_transactions):
    """Test AI classification task progress updates"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.ai.service.classify_transactions_batch') as mock_classify:
        mock_classify.return_value = {
            "import_id": "import123",
            "total_processed": 2,
            "classified": 2
        }
        
        classify_import_transactions(mock_task, "import123", "user123")
        
        # Check that progress was updated
        mock_task.update_state.assert_called()


# ============= Forecast Regeneration Task Tests =============

@pytest.mark.asyncio
async def test_regenerate_forecast_task(test_user):
    """Test forecast regeneration task"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.ai.forecasting.generate_cashflow_forecast') as mock_forecast:
        mock_forecast.return_value = {
            "current_balance": 5000.0,
            "forecast": [{"date": "2024-02-01", "projected_balance": 5200.0}],
            "risk_alert": None,
            "confidence": 0.8
        }
        
        result = regenerate_forecast(mock_task, "user123")
        
        assert result["user_id"] == "user123"
        assert result["forecast_generated"] is True
        assert result["has_risk"] is False


@pytest.mark.asyncio
async def test_regenerate_forecast_task_with_risk(test_user):
    """Test forecast regeneration task with risk alert"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.ai.forecasting.generate_cashflow_forecast') as mock_forecast:
        mock_forecast.return_value = {
            "current_balance": 500.0,
            "forecast": [{"date": "2024-02-15", "projected_balance": -100.0}],
            "risk_alert": {"has_risk": True, "message": "Cash may go negative"},
            "confidence": 0.7
        }
        
        result = regenerate_forecast(mock_task, "user123")
        
        assert result["has_risk"] is True


# ============= Anomaly Detection Task Tests =============

@pytest.mark.asyncio
async def test_run_anomaly_detection_task(test_user, sample_transactions):
    """Test anomaly detection background task"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.ai.forecasting.detect_anomalies') as mock_detect:
        mock_detect.return_value = [
            {
                "transaction_id": "tx1",
                "description": "AMZN MKTP US",
                "amount": -45.50,
                "z_score": 2.5,
                "category_id": "cat1"
            }
        ]
        
        with patch('app.tasks.alerts_collection') as mock_alerts:
            mock_alerts.find_one.return_value = None
            mock_alerts.insert_one.return_value = Mock()
            
            result = run_anomaly_detection(mock_task, "user123")
            
            assert result["user_id"] == "user123"
            assert result["anomalies_detected"] == 1
            assert result["alerts_created"] == 1


@pytest.mark.asyncio
async def test_run_anomaly_detection_no_anomalies(test_user):
    """Test anomaly detection with no anomalies found"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.ai.forecasting.detect_anomalies') as mock_detect:
        mock_detect.return_value = []
        
        result = run_anomaly_detection(mock_task, "user123")
        
        assert result["anomalies_detected"] == 0
        assert result["alerts_created"] == 0


# ============= Weekly Summary Task Tests =============

@pytest.mark.asyncio
async def test_generate_weekly_summary_task(test_user):
    """Test weekly summary generation task"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    # Mock transaction aggregation
    current_week = {"revenue": 5000, "expenses": 2000}
    prev_week = {"revenue": 4000, "expenses": 1800}
    
    with patch('app.tasks.transactions_collection') as mock_tx:
        mock_tx.aggregate.side_effect = [
            [{"_id": None, "revenue": 5000, "expenses": 2000}],  # Current week
            [{"_id": None, "revenue": 4000, "expenses": 1800}]   # Previous week
        ]
        
        with patch('app.tasks.entities_collection') as mock_entities:
            mock_entities.find_one.return_value = {"name": "ABC Corp"}
            
            with patch('app.tasks.groq_client') as mock_groq:
                mock_groq.generate_weekly_summary.return_value = {
                    "narrative": "Good week with revenue growth",
                    "recommendations": ["Keep up the good work"]
                }
                
                with patch('app.tasks.insights_collection') as mock_insights:
                    mock_insights.insert_one.return_value = Mock()
                    
                    result = generate_weekly_summary(mock_task, "user123")
                    
                    assert result["user_id"] == "user123"
                    assert result["summary_generated"] is True
                    assert result["revenue"] == 5000
                    assert result["expenses"] == 2000


@pytest.mark.asyncio
async def test_generate_weekly_summary_task_no_data(test_user):
    """Test weekly summary with no transaction data"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.tasks.transactions_collection') as mock_tx:
        mock_tx.aggregate.side_effect = [
            [],  # Current week empty
            []   # Previous week empty
        ]
        
        with patch('app.tasks.groq_client') as mock_groq:
            mock_groq.generate_weekly_summary.return_value = {
                "narrative": "No transactions this week",
                "recommendations": []
            }
            
            with patch('app.tasks.insights_collection') as mock_insights:
                mock_insights.insert_one.return_value = Mock()
                
                result = generate_weekly_summary(mock_task, "user123")
                
                assert result["user_id"] == "user123"
                assert result["revenue"] == 0
                assert result["expenses"] == 0


# ============= Task Error Handling Tests =============

@pytest.mark.asyncio
async def test_task_error_handling(test_user, sample_import):
    """Test task error handling"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.tasks.csv_imports') as mock_collection:
        mock_collection.find_one.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            process_csv_import(mock_task, "import123", "user123")


@pytest.mark.asyncio
async def test_task_import_status_update_on_error(test_user, sample_import):
    """Test that import status is updated to failed on error"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.tasks.csv_imports') as mock_collection:
        mock_collection.find_one.return_value = sample_import
        mock_collection.update_one.return_value = Mock()
        
        with patch('app.tasks.ingestion_service') as mock_service:
            mock_service.process_csv.side_effect = Exception("Processing error")
            
            with pytest.raises(Exception):
                process_csv_import(mock_task, "import123", "user123")
            
            # Verify status was updated to failed
            mock_collection.update_one.assert_any_call(
                {"_id": "import123"},
                {"$set": {
                    "status": "failed",
                    "error_message": "Processing error"
                }}
            )


# ============= Task Integration Tests =============

@pytest.mark.asyncio
async def test_task_chain_import_to_classification(test_user, sample_import, sample_transactions):
    """Test that import task triggers classification task"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.tasks.csv_imports') as mock_collection:
        mock_collection.find_one.return_value = sample_import
        mock_collection.update_one.return_value = Mock()
        
        with patch('app.tasks.ingestion_service') as mock_service:
            mock_service.process_csv = AsyncMock(return_value=sample_import)
            
            with patch('app.tasks.classify_transactions') as mock_classify:
                mock_task_instance = Mock()
                mock_task_instance.delay.return_value = Mock(id="task123")
                mock_classify.delay = mock_task_instance.delay
                
                result = process_csv_import(mock_task, "import123", "user123")
                
                assert result["status"] == "completed"
                mock_task_instance.delay.assert_called_once_with("import123", "user123")


# ============= Task Performance Tests =============

@pytest.mark.asyncio
async def test_task_progress_updates(test_user, sample_transactions):
    """Test that tasks update progress during processing"""
    mock_task = Mock()
    mock_task.update_state = Mock()
    
    with patch('app.ai.service.classify_transactions_batch') as mock_classify:
        mock_classify.return_value = {
            "import_id": "import123",
            "total_processed": 100,
            "classified": 95
        }
        
        classify_import_transactions(mock_task, "import123", "user123")
        
        # Verify progress was updated at least once
        mock_task.update_state.assert_called()


# Cleanup
@pytest.mark.asyncio
async def cleanup_task_test_data():
    """Clean up task test data"""
    await users.delete_many({"email": "test_tasks@example.com"})
    await csv_imports.delete_many({"filename": "test.csv"})
    await transactions.delete_many({"user_id": "user123"})
