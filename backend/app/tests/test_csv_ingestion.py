import pytest
import io
import csv
from fastapi.testclient import TestClient
from app.main import app
from app.database import csv_imports, transactions, users
from app.models.user import UserCreate

client = TestClient(app)

@pytest.fixture
async def test_user():
    """Create and authenticate a test user"""
    user_data = UserCreate(
        email="test@example.com",
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
def sample_csv_content():
    """Generate sample CSV content"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Date", "Description", "Amount", "Balance"])
    
    # Write sample data
    writer.writerow(["2024-01-15", "ACME Corp Payment", "1250.00", "15400.00"])
    writer.writerow(["2024-01-16", "Office Supplies", "-45.50", "15354.50"])
    writer.writerow(["2024-01-17", "Client B Invoice", "3200.00", "18554.50"])
    writer.writerow(["2024-01-18", "Software License", "-99.00", "18455.50"])
    
    return output.getvalue()

@pytest.fixture
def sample_csv_file(sample_csv_content):
    """Create a sample CSV file for upload"""
    return ("sample_transactions.csv", sample_csv_content, "text/csv")

@pytest.mark.asyncio
async def test_upload_csv_success(test_user, sample_csv_file):
    """Test successful CSV upload"""
    filename, content, content_type = sample_csv_file
    
    response = client.post(
        "/api/v1/imports/upload",
        files={"file": (filename, content, content_type)},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == filename
    assert data["status"] in ["pending", "processing", "preview_ready"]
    assert "id" in data

@pytest.mark.asyncio
async def test_upload_invalid_file_type(test_user):
    """Test upload of non-CSV file"""
    response = client.post(
        "/api/v1/imports/upload",
        files={"file": ("test.txt", "This is not a CSV", "text/plain")},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 400
    assert "csv files" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_upload_oversized_file(test_user):
    """Test upload of oversized file"""
    # Create a large file content (over 10MB)
    large_content = "x" * (11 * 1024 * 1024)  # 11MB
    
    response = client.post(
        "/api/v1/imports/upload",
        files={"file": ("large.csv", large_content, "text/csv")},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_import_preview(test_user, sample_csv_file):
    """Test getting import preview"""
    # Upload CSV first
    filename, content, content_type = sample_csv_file
    upload_response = client.post(
        "/api/v1/imports/upload",
        files={"file": (filename, content, content_type)},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    import_id = upload_response.json()["id"]
    
    # Get preview
    response = client.get(
        f"/api/v1/imports/{import_id}/preview",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "column_mapping" in data
    assert "detection_confidence" in data
    assert "rows" in data
    assert "validation_summary" in data
    assert len(data["rows"]) > 0

@pytest.mark.asyncio
async def test_update_column_mapping(test_user, sample_csv_file):
    """Test updating column mapping"""
    # Upload CSV first
    filename, content, content_type = sample_csv_file
    upload_response = client.post(
        "/api/v1/imports/upload",
        files={"file": (filename, content, content_type)},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    import_id = upload_response.json()["id"]
    
    # Update column mapping
    mapping = {
        "date": "Date",
        "description": "Description", 
        "amount": "Amount",
        "debit": None,
        "credit": None,
        "balance": "Balance"
    }
    
    response = client.put(
        f"/api/v1/imports/{import_id}/column-mapping",
        json=mapping,
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["column_mapping"]["date"] == "Date"
    assert data["column_mapping"]["description"] == "Description"

@pytest.mark.asyncio
async def test_confirm_import(test_user, sample_csv_file):
    """Test confirming import"""
    # Upload CSV first
    filename, content, content_type = sample_csv_file
    upload_response = client.post(
        "/api/v1/imports/upload",
        files={"file": (filename, content, content_type)},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    import_id = upload_response.json()["id"]
    
    # Confirm import
    response = client.post(
        f"/api/v1/imports/{import_id}/confirm",
        json={"duplicate_action": "skip"},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "imported_count" in data
    assert "transactions" in data
    assert data["imported_count"] > 0

@pytest.mark.asyncio
async def test_get_imports_list(test_user, sample_csv_file):
    """Test getting list of imports"""
    # Upload a CSV first
    filename, content, content_type = sample_csv_file
    client.post(
        "/api/v1/imports/upload",
        files={"file": (filename, content, content_type)},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Get imports list
    response = client.get(
        "/api/v1/imports/",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.asyncio
async def test_import_without_auth(sample_csv_file):
    """Test import operations without authentication"""
    filename, content, content_type = sample_csv_file
    
    # Try to upload without auth
    response = client.post(
        "/api/v1/imports/upload",
        files={"file": (filename, content, content_type)}
    )
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_column_detection_accuracy():
    """Test column detection accuracy"""
    # This would test the CSV processor's column detection logic
    # For now, we'll test with a well-formatted CSV
    csv_content = """Date,Description,Amount,Balance
2024-01-15,ACME Corp Payment,1250.00,15400.00
2024-01-16,Office Supplies,-45.50,15354.50
2024-01-17,Client B Invoice,3200.00,18554.50"""
    
    response = client.post(
        "/api/v1/imports/upload",
        files={"file": ("test.csv", csv_content, "text/csv")},
        headers={"Authorization": f"Bearer {(await test_user)['token']}"}
    )
    
    import_id = response.json()["id"]
    
    preview_response = client.get(
        f"/api/v1/imports/{import_id}/preview",
        headers={"Authorization": f"Bearer {(await test_user)['token']}"}
    )
    
    preview_data = preview_response.json()
    
    # Should detect columns with high confidence
    assert preview_data["detection_confidence"] > 0.8
    assert preview_data["column_mapping"]["date"] == "Date"
    assert preview_data["column_mapping"]["description"] == "Description"
    assert preview_data["column_mapping"]["amount"] == "Amount"

# Cleanup
@pytest.mark.asyncio
async def cleanup_test_data():
    """Clean up test data"""
    await users.delete_many({"email": {"$regex": r"^test"}})
    await csv_imports.delete_many({})
    await transactions.delete_many({})
