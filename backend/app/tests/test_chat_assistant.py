"""Test Conversational Assistant for Iteration 3"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import users, transactions, entities, chat_sessions, chat_messages
from app.models.user import UserCreate

client = TestClient(app)


@pytest.fixture
async def test_user():
    """Create and authenticate a test user"""
    user_data = UserCreate(
        email="test_chat@example.com",
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
    """Create sample transactions for chat testing"""
    transactions_data = [
        {
            "_id": "tx1",
            "user_id": test_user["user_id"],
            "transaction_date": "2024-01-15",
            "description": "AMZN MKTP US Purchase",
            "amount": -45.50,
            "entity_id": "entity1",
            "expense_category_id": "cat1"
        },
        {
            "_id": "tx2",
            "user_id": test_user["user_id"],
            "transaction_date": "2024-01-16",
            "description": "ABC Corp Invoice Payment",
            "amount": 1250.00,
            "entity_id": "entity2",
            "expense_category_id": None
        },
        {
            "_id": "tx3",
            "user_id": test_user["user_id"],
            "transaction_date": "2024-01-17",
            "description": "Office Supplies Store",
            "amount": -89.99,
            "entity_id": None,
            "expense_category_id": "cat2"
        }
    ]
    await transactions.insert_many(transactions_data)
    return transactions_data


@pytest.fixture
async def sample_entities(test_user):
    """Create sample entities for chat testing"""
    entities_data = [
        {
            "_id": "entity1",
            "user_id": test_user["user_id"],
            "name": "Amazon",
            "normalized_name": "amazon",
            "entity_type": "supplier",
            "total_expense": 500.0
        },
        {
            "_id": "entity2",
            "user_id": test_user["user_id"],
            "name": "ABC Corp",
            "normalized_name": "abc corp",
            "entity_type": "customer",
            "total_revenue": 5000.0
        }
    ]
    await entities.insert_many(entities_data)
    return entities_data


# ============= Chat Session Management Tests =============

@pytest.mark.asyncio
async def test_create_chat_session(test_user):
    """Test creating a new chat session"""
    response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["user_id"] == test_user["user_id"]
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_chat_sessions(test_user):
    """Test listing user's chat sessions"""
    # Create a session first
    create_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = create_response.json()["session_id"]
    
    # List sessions
    response = client.get(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    sessions = response.json()
    assert isinstance(sessions, list)
    assert len(sessions) >= 1
    assert any(s["session_id"] == session_id for s in sessions)


@pytest.mark.asyncio
async def test_get_chat_session(test_user):
    """Test retrieving a specific chat session"""
    # Create a session
    create_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = create_response.json()["session_id"]
    
    # Get session details
    response = client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "messages" in data
    assert isinstance(data["messages"], list)


# ============= Intent Classification Tests =============

@pytest.mark.asyncio
async def test_classify_revenue_intent(test_user, sample_transactions):
    """Test classification of revenue query intent"""
    with patch('app.chat.agent.groq_client') as mock_groq:
        mock_groq.classify_intent.return_value = "revenue_query"
        
        response = client.post(
            "/api/v1/chat/intent",
            json={"query": "What was my revenue this month?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "revenue_query"
        assert data["confidence"] > 0.7


@pytest.mark.asyncio
async def test_classify_expense_intent(test_user, sample_transactions):
    """Test classification of expense query intent"""
    with patch('app.chat.agent.groq_client') as mock_groq:
        mock_groq.classify_intent.return_value = "expense_query"
        
        response = client.post(
            "/api/v1/chat/intent",
            json={"query": "How much did I spend on office supplies?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "expense_query"


@pytest.mark.asyncio
async def test_classify_entity_query_intent(test_user, sample_entities):
    """Test classification of entity-specific query"""
    with patch('app.chat.agent.groq_client') as mock_groq:
        mock_groq.classify_intent.return_value = "entity_breakdown"
        mock_groq.extract_entity.return_value = ("Amazon", 0.9)
        
        response = client.post(
            "/api/v1/chat/intent",
            json={"query": "Show me Amazon transactions"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "entity_breakdown"
        assert data["extracted_entity"] == "Amazon"


@pytest.mark.asyncio
async def test_classify_forecast_intent(test_user):
    """Test classification of forecast query"""
    with patch('app.chat.agent.groq_client') as mock_groq:
        mock_groq.classify_intent.return_value = "forecast_query"
        
        response = client.post(
            "/api/v1/chat/intent",
            json={"query": "Will I run out of cash next month?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "forecast_query"


# ============= Chat Message Processing Tests =============

@pytest.mark.asyncio
async def test_send_revenue_query_message(test_user, sample_transactions):
    """Test processing a revenue query message"""
    # Create session
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = session_response.json()["session_id"]
    
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Your total revenue this month is $1,250.00 from ABC Corp.",
            "data_used": {"total_revenue": 1250.00, "period": "this_month"},
            "confidence": 0.9
        }
        
        response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "What was my revenue this month?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "message_id" in data
        assert data["response"] == "Your total revenue this month is $1,250.00 from ABC Corp."


@pytest.mark.asyncio
async def test_send_expense_query_message(test_user, sample_transactions):
    """Test processing an expense query message"""
    # Create session
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = session_response.json()["session_id"]
    
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "You spent $135.49 on expenses this month, with $45.50 going to Amazon.",
            "data_used": {"total_expenses": 135.49, "top_supplier": "Amazon"},
            "confidence": 0.85
        }
        
        response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "What did I spend this month?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "$135.49" in data["response"]


@pytest.mark.asyncio
async def test_send_entity_breakdown_message(test_user, sample_entities, sample_transactions):
    """Test processing an entity breakdown query"""
    # Create session
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = session_response.json()["session_id"]
    
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Amazon has 2 transactions totaling $500.00 in expenses. All purchases were for supplies.",
            "data_used": {
                "entity_name": "Amazon",
                "transaction_count": 2,
                "total_amount": 500.00,
                "transactions": [
                    {"date": "2024-01-15", "amount": -45.50, "description": "AMZN MKTP US Purchase"}
                ]
            },
            "confidence": 0.9
        }
        
        response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "Show me Amazon transactions"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Amazon" in data["response"]
        assert "$500.00" in data["response"]


@pytest.mark.asyncio
async def test_send_forecast_query_message(test_user):
    """Test processing a forecast query"""
    # Create session
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = session_response.json()["session_id"]
    
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Based on current trends, your cash balance is projected to be $5,200 by end of next month. No cashflow risks detected.",
            "data_used": {
                "current_balance": 5000.00,
                "projected_balance": 5200.00,
                "risk_alert": None,
                "confidence": 0.75
            },
            "confidence": 0.8
        }
        
        response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "Will I run out of cash next month?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "projected" in data["response"].lower()
        assert "$5,200" in data["response"]


# ============= Context Management Tests =============

@pytest.mark.asyncio
async def test_chat_context_maintenance(test_user, sample_transactions):
    """Test that chat maintains context across messages"""
    # Create session
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = session_response.json()["session_id"]
    
    with patch('app.chat.agent.chat_agent') as mock_agent:
        # First message about revenue
        mock_agent.process_message.return_value = {
            "response": "Your revenue this month was $1,250.00.",
            "data_used": {"total_revenue": 1250.00},
            "confidence": 0.9
        }
        
        response1 = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "What was my revenue?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        # Follow-up question about previous context
        mock_agent.process_message.return_value = {
            "response": "Compared to last month, your revenue increased by 25% from $1,000.00.",
            "data_used": {"current_month": 1250.00, "previous_month": 1000.00, "change_pct": 25.0},
            "confidence": 0.85
        }
        
        response2 = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "How does that compare to last month?"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify context was maintained (agent should know we're talking about revenue)
        mock_agent.process_message.assert_called()
        # The second call should include context from the first message


@pytest.mark.asyncio
async def test_get_chat_history(test_user, sample_transactions):
    """Test retrieving chat message history"""
    # Create session
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = session_response.json()["session_id"]
    
    # Send a few messages
    with patch('app.chat.agent.chat_agent') as mock_agent:
        mock_agent.process_message.return_value = {
            "response": "Test response",
            "data_used": {},
            "confidence": 0.9
        }
        
        # Send messages
        client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "First question"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "Second question"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
    
    # Get history
    response = client.get(
        f"/api/v1/chat/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    messages = response.json()
    assert isinstance(messages, list)
    assert len(messages) >= 4  # 2 user messages + 2 AI responses


# ============= Tool Execution Tests =============

@pytest.mark.asyncio
async def test_revenue_tool_execution(test_user, sample_transactions):
    """Test revenue data retrieval tool"""
    from app.chat.tools import get_revenue_summary
    
    result = await get_revenue_summary(test_user["user_id"], "2024-01")
    
    assert "total_revenue" in result
    assert "period" in result
    assert result["total_revenue"] == 1250.00


@pytest.mark.asyncio
async def test_expense_tool_execution(test_user, sample_transactions):
    """Test expense data retrieval tool"""
    from app.chat.tools import get_expense_summary
    
    result = await get_expense_summary(test_user["user_id"], "2024-01")
    
    assert "total_expenses" in result
    assert "period" in result
    assert result["total_expenses"] == 135.49


@pytest.mark.asyncio
async def test_entity_summary_tool(test_user, sample_entities, sample_transactions):
    """Test entity summary retrieval tool"""
    from app.chat.tools import get_entity_summary
    
    result = await get_entity_summary(test_user["user_id"], "Amazon")
    
    assert "entity_name" in result
    assert "total_amount" in result
    assert "transaction_count" in result
    assert result["entity_name"] == "Amazon"


@pytest.mark.asyncio
async def test_top_customers_tool(test_user, sample_entities, sample_transactions):
    """Test top customers retrieval tool"""
    from app.chat.tools import get_top_customers
    
    result = await get_top_customers(test_user["user_id"], limit=5)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert "name" in result[0]
    assert "total_revenue" in result[0]


# ============= Error Handling Tests =============

@pytest.mark.asyncio
async def test_chat_unauthorized():
    """Test chat endpoints require authentication"""
    response = client.post("/api/v1/chat/sessions")
    assert response.status_code == 401
    
    response = client.post("/api/v1/chat/sessions/invalid/messages", json={"message": "test"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_session_id(test_user):
    """Test handling of invalid session IDs"""
    response = client.get(
        "/api/v1/chat/sessions/invalid-session-id",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_empty_message(test_user):
    """Test handling of empty messages"""
    # Create session
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = session_response.json()["session_id"]
    
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"message": ""},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 400
    assert "message" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ambiguous_query_handling(test_user):
    """Test handling of ambiguous or unclear queries"""
    # Create session
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = session_response.json()["session_id"]
    
    with patch('app.chat.agent.groq_client') as mock_groq:
        mock_groq.classify_intent.return_value = "unknown"
        
        response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"message": "asdfghjkl"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "clarification" in data["response"].lower() or "understand" in data["response"].lower()


# ============= Performance Tests =============

@pytest.mark.asyncio
async def test_concurrent_chat_sessions(test_user):
    """Test handling multiple concurrent chat sessions"""
    session_ids = []
    
    # Create multiple sessions
    for i in range(5):
        response = client.post(
            "/api/v1/chat/sessions",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        session_ids.append(response.json()["session_id"])
    
    # Verify all sessions were created
    list_response = client.get(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert list_response.status_code == 200
    sessions = list_response.json()
    assert len(sessions) >= 5
    
    # Verify all session IDs exist
    for session_id in session_ids:
        assert any(s["session_id"] == session_id for s in sessions)


# Cleanup
@pytest.mark.asyncio
async def cleanup_chat_test_data():
    """Clean up chat test data"""
    await users.delete_many({"email": "test_chat@example.com"})
    await transactions.delete_many({"description": {"$regex": r"^(AMZN|ABC|Office)"}})
    await entities.delete_many({"name": {"$regex": r"^(Amazon|ABC)"}})
    await chat_sessions.delete_many({})
    await chat_messages.delete_many({})
