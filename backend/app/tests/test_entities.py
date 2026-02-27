import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import entities, transactions, users
from app.models.user import UserCreate
from app.models.entity import EntityCreate

client = TestClient(app)


@pytest.fixture
async def test_user():
    """Create and authenticate a test user"""
    user_data = UserCreate(
        email="test_entities@example.com",
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
async def sample_entity():
    """Sample entity data"""
    return EntityCreate(
        name="ACME Corporation",
        normalized_name="acme corporation",
        type="customer"
    )


@pytest.mark.asyncio
async def test_create_entity(test_user, sample_entity):
    """Test entity creation"""
    response = client.post(
        "/api/v1/entities/",
        json=sample_entity.dict(),
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_entity.name
    assert data["type"] == sample_entity.type
    assert "id" in data


@pytest.mark.asyncio
async def test_get_entities(test_user, sample_entity):
    """Test getting all entities"""
    # Create entity first
    create_response = client.post(
        "/api/v1/entities/",
        json=sample_entity.dict(),
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Get entities
    response = client.get(
        "/api/v1/entities/",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(entity["name"] == sample_entity.name for entity in data)


@pytest.mark.asyncio
async def test_get_top_customers(test_user):
    """Test getting top customers"""
    response = client.get(
        "/api/v1/entities/top-customers",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_top_suppliers(test_user):
    """Test getting top suppliers"""
    response = client.get(
        "/api/v1/entities/top-suppliers",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
