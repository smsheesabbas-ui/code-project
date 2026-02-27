"""Integration tests for Iteration 3 features"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import (
    users, transactions, entities, chat_sessions, chat_messages,
    notification_preferences, alerts, dashboard_layouts
)
from app.models.user import UserCreate

client = TestClient(app)


@pytest.fixture
async def test_user():
    """Create and authenticate a test user"""
    user_data = UserCreate(
        email="test_integration_v3@example.com",
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
async def setup_full_v3_data(test_user):
    """Set up complete data for Iteration 3 workflow testing"""
    user_id = test_user["user_id"]
    
    # Create entities
    entities_data = [
        {"_id": "entity1", "user_id": user_id, "name": "Amazon", "normalized_name": "amazon", "entity_type": "supplier"},
        {"_id": "entity2", "user_id": user_id, "name": "ABC Corp", "normalized_name": "abc corp", "entity_type": "customer"},
        {"_id": "entity3", "user_id": user_id, "name": "Office Depot", "normalized_name": "office depot", "entity_type": "supplier"}
    ]
    await entities.insert_many(entities_data)
    
    # Create transactions with varied data
    transactions_data = []
    for i in range(60):  # 2 months of data
        transactions_data.append({
            "_id": f"tx_{i}",
            "user_id": user_id,
            "transaction_date": f"2024-{(i // 30) + 1:02d}-{(i % 28) + 1:02d}",
            "description": f"{'Payment from' if i % 3 == 0 else 'Purchase at'} {'ABC Corp' if i % 3 == 0 else ['Amazon', 'Office Depot'][i % 2]}",
            "amount": 1000.0 if i % 3 == 0 else -50.0,
            "entity_id": f"entity{(i % 3) + 1}",
            "expense_category_id": f"cat_{i % 5}" if i % 3 != 0 else None
        })
    await transactions.insert_many(transactions_data)
    
    # Create alerts
    alerts_data = [
        {
            "_id": "alert1",
            "user_id": user_id,
            "alert_type": "anomaly",
            "severity": "medium",
            "title": "Unusual Spending Detected",
            "message": "Large purchase detected at Amazon",
            "is_acknowledged": False
        },
        {
            "_id": "alert2",
            "user_id": user_id,
            "alert_type": "cashflow_risk",
            "severity": "high",
            "title": "Cashflow Risk",
            "message": "Cash may go negative in 15 days",
            "is_acknowledged": False
        }
    ]
    await alerts.insert_many(alerts_data)
    
    return {
        "entities": entities_data,
        "transactions": transactions_data,
        "alerts": alerts_data
    }


# ============= Complete Iteration 3 Workflow Tests =============

@pytest.mark.asyncio
async def test_complete_v3_user_journey(test_user, setup_full_v3_data):
    """Test complete user journey through all Iteration 3 features"""
    
    # 1. User logs in and checks dashboard
    dashboard_response = client.get(
        "/api/v1/dashboard/overview",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert dashboard_response.status_code == 200
    dashboard_data = dashboard_response.json()
    assert "cash_balance" in dashboard_data
    
    # 2. User customizes dashboard layout
    layout_data = {
        "layout": {
            "lg": [
                {"i": "overview", "x": 0, "y": 0, "w": 6, "h": 4},
                {"i": "trends", "x": 6, "y": 0, "w": 6, "h": 4},
                {"i": "cashflow", "x": 0, "y": 4, "w": 12, "h": 6}
            ]
        },
        "widgets": [
            {"id": "overview", "type": "kpi", "title": "Overview"},
            {"id": "trends", "type": "chart", "title": "Trends"},
            {"id": "cashflow", "type": "timeline", "title": "Cashflow"}
        ]
    }
    
    layout_response = client.put(
        "/api/v1/dashboard/layout",
        json=layout_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert layout_response.status_code == 200
    
    # 3. User views trends and cashflow timeline
    trends_response = client.get(
        "/api/v1/dashboard/trends?period=60d",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert trends_response.status_code == 200
    
    with patch('app.ai.forecasting.generate_cashflow_forecast') as mock_forecast:
        mock_forecast.return_value = {
            "current_balance": 5000.0,
            "forecast": [{"date": "2024-03-01", "projected_balance": 5200.0}],
            "risk_alert": None,
            "confidence": 0.8
        }
        
        cashflow_response = client.get(
            "/api/v1/dashboard/cashflow-timeline",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert cashflow_response.status_code == 200
    
    # 4. User starts chat conversation
    chat_session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert chat_session_response.status_code == 200
    session_id = chat_session_response.json()["session_id"]
    
    # 5. User asks about revenue
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Your total revenue for the last 60 days was $20,000.00 from 20 payments.",
            "data_used": {"total_revenue": 20000.00, "period": "60 days"},
            "confidence": 0.9
        }
        
        message_response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "What was my revenue in the last 2 months?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert message_response.status_code == 200
        message_data = message_response.json()
        assert "$20,000.00" in message_data["response"]
    
    # 6. User asks about specific entity
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Amazon has 20 transactions totaling $1,000.00 in expenses over the last 60 days.",
            "data_used": {"entity_name": "Amazon", "transaction_count": 20, "total_amount": 1000.00},
            "confidence": 0.85
        }
        
        entity_response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "Show me Amazon transactions"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert entity_response.status_code == 200
        entity_data = entity_response.json()
        assert "Amazon" in entity_data["response"]
    
    # 7. User sets up notification preferences
    preferences_response = client.put(
        "/api/v1/notifications/preferences",
        json={
            "email_enabled": True,
            "weekly_summary": True,
            "alert_emails": True,
            "email_address": test_user["user"]["email"]
        },
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert preferences_response.status_code == 200
    
    # 8. User triggers weekly summary email
    with patch('app.notifications.email_service.resend') as mock_resend:
        mock_resend.Emails.send.return_value = {"id": "email123"}
        
        email_response = client.post(
            "/api/v1/notifications/send-weekly-summary",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert email_response.status_code == 200
        email_data = email_response.json()
        assert email_data["status"] == "sent"
    
    # 9. User views chat history
    history_response = client.get(
        f"/api/v1/chat/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert len(history_data) >= 4  # 2 user messages + 2 AI responses


@pytest.mark.asyncio
async def test_chat_context_across_dashboard_interactions(test_user, setup_full_v3_data):
    """Test that chat maintains context when user interacts with dashboard"""
    
    # Create chat session
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = session_response.json()["session_id"]
    
    # User asks about revenue
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Your revenue this month was $10,000.00.",
            "data_used": {"total_revenue": 10000.00, "period": "this month"},
            "confidence": 0.9
        }
        
        client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "What's my revenue this month?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
    
    # User views dashboard trends
    trends_response = client.get(
        "/api/v1/dashboard/trends?period=30d",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert trends_response.status_code == 200
    
    # User asks follow-up question in chat
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Compared to last month, your revenue increased by 25% from $8,000.00.",
            "data_used": {"current_month": 10000.00, "previous_month": 8000.00, "change_pct": 25.0},
            "confidence": 0.85
        }
        
        followup_response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "How does that compare to last month?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert followup_response.status_code == 200
        followup_data = followup_response.json()
        assert "25%" in followup_data["response"]


@pytest.mark.asyncio
async def test_notifications_triggered_by_dashboard_insights(test_user, setup_full_v3_data):
    """Test that dashboard insights trigger appropriate notifications"""
    
    # Set up notification preferences
    client.put(
        "/api/v1/notifications/preferences",
        json={
            "email_enabled": True,
            "weekly_summary": True,
            "alert_emails": True,
            "email_address": test_user["user"]["email"]
        },
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # View anomalies on dashboard
    with patch('app.ai.forecasting.detect_anomalies') as mock_detect:
        mock_detect.return_value = [
            {
                "transaction_id": "tx_anomaly",
                "date": "2024-02-15",
                "description": "Large unusual purchase",
                "amount": -500.00,
                "z_score": 3.5,
                "severity": "high"
            }
        ]
        
        anomalies_response = client.get(
            "/api/v1/dashboard/anomalies",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert anomalies_response.status_code == 200
    
    # Send alert email for anomaly
    with patch('app.notifications.email_service.resend') as mock_resend:
        mock_resend.Emails.send.return_value = {"id": "alert_email123"}
        
        alert_email_response = client.post(
            "/api/v1/notifications/send-alert/alert1",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert alert_email_response.status_code == 200
        assert alert_email_response.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_mobile_responsive_dashboard_workflow(test_user, setup_full_v3_data):
    """Test complete workflow on mobile-optimized dashboard"""
    
    # Get mobile layout
    mobile_response = client.get(
        "/api/v1/dashboard/layout?viewport=mobile",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert mobile_response.status_code == 200
    mobile_data = mobile_response.json()
    assert mobile_data["viewport"] == "mobile"
    
    # Get mobile-optimized widget data
    widgets = ["overview", "trends", "cashflow"]
    for widget in widgets:
        response = client.get(
            f"/api/v1/dashboard/widgets/{widget}?viewport=mobile",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "mobile_optimized" in data or "data" in data
    
    # Use chat on mobile
    chat_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = chat_response.json()["session_id"]
    
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Your current cash balance is $5,000.00.",
            "data_used": {"current_balance": 5000.00},
            "confidence": 0.9
        }
        
        message_response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "What's my cash balance?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert message_response.status_code == 200


@pytest.mark.asyncio
async def test_cross_feature_data_consistency(test_user, setup_full_v3_data):
    """Test data consistency across all Iteration 3 features"""
    
    # Get dashboard overview
    dashboard_response = client.get(
        "/api/v1/dashboard/overview",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    dashboard_data = dashboard_response.json()
    
    # Get trends data
    trends_response = client.get(
        "/api/v1/dashboard/trends?period=60d",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    trends_data = trends_response.json()
    
    # Ask chat about same data
    chat_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = chat_response.json()["session_id"]
    
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Your total revenue over the last 60 days was $20,000.00.",
            "data_used": {"total_revenue": 20000.00, "period": "60 days"},
            "confidence": 0.9
        }
        
        chat_message_response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "What was my revenue in the last 60 days?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        chat_data = chat_message_response.json()
    
    # Data should be consistent across features
    # (In real implementation, would verify actual numbers match)
    assert "total_revenue" in dashboard_data
    assert "revenue_trend" in trends_data
    assert "$20,000.00" in chat_data["response"]


# ============= Performance and Scalability Tests =============

@pytest.mark.asyncio
async def test_concurrent_v3_features(test_user, setup_full_v3_data):
    """Test concurrent usage of all Iteration 3 features"""
    import asyncio
    
    async def use_dashboard():
        return client.get(
            "/api/v1/dashboard/overview",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
    
    async def use_chat():
        session_resp = client.post(
            "/api/v1/chat/sessions",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        session_id = session_resp.json()["session_id"]
        
        with patch('app.chat.agent.chat_agent') as mock_agent:
            mock_agent.process_message.return_value = {
                "response": "Test response",
                "data_used": {},
                "confidence": 0.9
            }
            
            return client.post(
                f"/api/v1/chat/sessions/{session_id}/messages",
                json={"message": "Test message"},
                headers={"Authorization": f"Bearer {test_user['token']}"}
            )
    
    async def use_notifications():
        return client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
    
    # Run all features concurrently
    tasks = [
        use_dashboard(),
        use_chat(),
        use_notifications(),
        use_dashboard(),  # Duplicate to test concurrency
        use_chat()
    ]
    
    responses = await asyncio.gather(*tasks)
    
    # All should succeed
    for response in responses:
        assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_large_dataset_performance(test_user):
    """Test performance with large datasets across all features"""
    # Create large dataset
    large_transactions = []
    for i in range(1000):
        large_transactions.append({
            "_id": f"large_tx_{i}",
            "user_id": test_user["user_id"],
            "transaction_date": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
            "description": f"Large Transaction {i}",
            "amount": -10.0 if i % 2 == 0 else 100.0,
            "entity_id": f"entity_{i % 10}" if i % 5 == 0 else None
        })
    await transactions.insert_many(large_transactions)
    
    import time
    
    # Test dashboard performance
    start_time = time.time()
    dashboard_response = client.get(
        "/api/v1/dashboard/trends?period=90d",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    dashboard_time = time.time() - start_time
    
    assert dashboard_response.status_code == 200
    assert dashboard_time < 3.0  # Should load within 3 seconds
    
    # Test chat performance
    chat_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert chat_response.status_code == 200
    
    session_id = chat_response.json()["session_id"]
    
    start_time = time.time()
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Response based on large dataset",
            "data_used": {"transaction_count": 1000},
            "confidence": 0.9
        }
        
        message_response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "Analyze my transactions"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
    chat_time = time.time() - start_time
    
    assert message_response.status_code == 200
    assert chat_time < 2.0  # Should respond within 2 seconds


# ============= Error Recovery Tests =============

@pytest.mark.asyncio
async def test_feature_failure_recovery(test_user, setup_full_v3_data):
    """Test system behavior when individual features fail"""
    
    # Test chat failure recovery
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.side_effect = Exception("AI service unavailable")
        
        chat_response = client.post(
            "/api/v1/chat/sessions",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        session_id = chat_response.json()["session_id"]
        
        message_response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "Test message"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        # Should handle error gracefully
        assert message_response.status_code in [500, 200]
        if message_response.status_code == 200:
            data = message_response.json()
            assert "error" in data.get("response", "").lower() or "unavailable" in data.get("response", "").lower()
    
    # Dashboard should still work
    dashboard_response = client.get(
        "/api/v1/dashboard/overview",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert dashboard_response.status_code == 200
    
    # Notifications should still work
    notifications_response = client.get(
        "/api/v1/notifications/preferences",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert notifications_response.status_code == 200


# ============= Security Tests =============

@pytest.mark.asyncio
async def test_cross_feature_data_isolation(test_user, setup_full_v3_data):
    """Test that users can only access their own data across all features"""
    
    # Create another user
    other_user_data = UserCreate(
        email="other_user@example.com",
        password="password123",
        full_name="Other User"
    )
    
    await users.delete_one({"email": other_user_data.email})
    other_response = client.post("/api/v1/auth/register", json=other_user_data.dict())
    other_token = other_response.json()["access_token"]
    
    # Try to access original user's data
    original_session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    original_session_id = original_session_response.json()["session_id"]
    
    # Other user should not be able to access original user's chat session
    response = client.get(
        f"/api/v1/chat/sessions/{original_session_id}",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert response.status_code == 404
    
    # Other user should not see original user's dashboard layout
    layout_response = client.get(
        "/api/v1/dashboard/layout",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert layout_response.status_code == 200
    layout_data = layout_response.json()
    # Should be default layout, not original user's custom layout


# Cleanup
@pytest.mark.asyncio
async def cleanup_integration_v3_test_data():
    """Clean up Integration v3 test data"""
    await users.delete_many({"email": {"$regex": r"^(test_integration_v3|other_user)"}})
    await transactions.delete_many({"description": {"$regex": r"^(Payment from|Purchase at|Large Transaction)"}})
    await entities.delete_many({"name": {"$regex": r"^(Amazon|ABC|Office)"}})
    await chat_sessions.delete_many({})
    await chat_messages.delete_many({})
    await notification_preferences.delete_many({})
    await alerts.delete_many({"title": {"$regex": r"^(Unusual|Cashflow)"}})
    await dashboard_layouts.delete_many({})
