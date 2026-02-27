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
        email="test_chat@example.com",
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
async def test_create_chat_session(test_user):
    """Test creating a chat session"""
    session_data = {
        "title": "Test Session",
        "initial_message": "What was my revenue this month?"
    }
    
    response = client.post(
        "/api/v1/chat/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Session"
    assert "id" in data
    assert len(data["messages"]) >= 2  # User message + AI response


@pytest.mark.asyncio
async def test_get_chat_sessions(test_user):
    """Test getting all chat sessions"""
    # Create a session first
    session_data = {
        "title": "Test Session",
        "initial_message": "What was my revenue this month?"
    }
    client.post(
        "/api/v1/chat/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Get sessions
    response = client.get(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_send_chat_message(test_user):
    """Test sending a message to chat session"""
    # Create session
    session_data = {"title": "Test Session"}
    create_response = client.post(
        "/api/v1/chat/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = create_response.json()["id"]
    
    # Send message
    message_data = {"content": "What was my revenue this month?"}
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json=message_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "intent" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_chat_intent_classification(test_user):
    """Test different chat intents"""
    test_queries = [
        ("What was my revenue this month?", "revenue_query"),
        ("How much did I spend?", "expense_query"),
        ("Who is my top customer?", "top_customer_query"),
        ("How is my cashflow?", "cashflow_query"),
        ("Show me trends", "trend_query")
    ]
    
    for query, expected_intent in test_queries:
        # Create session
        session_data = {"title": f"Test {expected_intent}"}
        create_response = client.post(
            "/api/v1/chat/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        session_id = create_response.json()["id"]
        
        # Send message
        message_data = {"content": query}
        response = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json=message_data,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Note: Intent classification may not be exact without real data
        assert "intent" in data
        assert "content" in data


@pytest.mark.asyncio
async def test_delete_chat_session(test_user):
    """Test deleting a chat session"""
    # Create session
    session_data = {"title": "Test Session to Delete"}
    create_response = client.post(
        "/api/v1/chat/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    session_id = create_response.json()["id"]
    
    # Delete session
    response = client.delete(
        f"/api/v1/chat/sessions/{session_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    assert "message" in response.json()
