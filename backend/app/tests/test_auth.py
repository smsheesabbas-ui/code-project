import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import users
from app.models.user import UserCreate

client = TestClient(app)

@pytest.fixture
async def test_user():
    """Create a test user for testing"""
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    
    # Clean up any existing user
    await users.delete_one({"email": user_data.email})
    
    return user_data

@pytest.mark.asyncio
async def test_register_user(test_user):
    """Test user registration"""
    response = client.post("/api/v1/auth/register", json={
        "email": test_user.email,
        "password": test_user.password,
        "full_name": test_user.full_name
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert "id" in data
    assert "access_token" in data

@pytest.mark.asyncio
async def test_register_duplicate_email(test_user):
    """Test registration with duplicate email"""
    # Register first user
    client.post("/api/v1/auth/register", json={
        "email": test_user.email,
        "password": test_user.password,
        "full_name": test_user.full_name
    })
    
    # Try to register same email again
    response = client.post("/api/v1/auth/register", json={
        "email": test_user.email,
        "password": "differentpassword",
        "full_name": "Different User"
    })
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_success(test_user):
    """Test successful login"""
    # Register user first
    client.post("/api/v1/auth/register", json={
        "email": test_user.email,
        "password": test_user.password,
        "full_name": test_user.full_name
    })
    
    # Login
    response = client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": test_user.password
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token"""
    response = client.get("/api/v1/dashboard/overview")
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(test_user):
    """Test accessing protected endpoint with valid token"""
    # Register and login
    register_response = client.post("/api/v1/auth/register", json={
        "email": test_user.email,
        "password": test_user.password,
        "full_name": test_user.full_name
    })
    
    token = register_response.json()["access_token"]
    
    # Access protected endpoint
    response = client.get("/api/v1/dashboard/overview", headers={
        "Authorization": f"Bearer {token}"
    })
    
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token():
    """Test accessing protected endpoint with invalid token"""
    response = client.get("/api/v1/dashboard/overview", headers={
        "Authorization": "Bearer invalid_token"
    })
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_logout(test_user):
    """Test logout functionality"""
    # Register and login
    register_response = client.post("/api/v1/auth/register", json={
        "email": test_user.email,
        "password": test_user.password,
        "full_name": test_user.full_name
    })
    
    token = register_response.json()["access_token"]
    
    # Logout
    response = client.post("/api/v1/auth/logout", headers={
        "Authorization": f"Bearer {token}"
    })
    
    assert response.status_code == 200
    assert "successfully" in response.json()["message"].lower()

# Cleanup
@pytest.mark.asyncio
async def cleanup_test_data():
    """Clean up test data"""
    await users.delete_many({"email": {"$regex": r"^test"}})
