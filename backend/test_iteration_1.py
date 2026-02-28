"""
Iteration 1 Comprehensive Test Suite
Tests all core functionality implemented in Iteration 1:
- Authentication (JWT)
- CSV Upload and Processing
- Transaction Management
- Dashboard Analytics
"""

import pytest
import asyncio
import os
import tempfile
import csv
import json
from datetime import datetime, date
from fastapi.testclient import TestClient
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from app.main import app
from app.core.config import settings
from app.core.auth import get_password_hash
from app.core.database import get_database


class TestIteration1Authentication:
    """Test authentication endpoints and JWT functionality"""
    
    @pytest.fixture
    async def test_user(self):
        """Create test user for authentication tests"""
        db = get_database()
        
        # Clean up any existing test user
        await db.users.delete_many({"email": "test@example.com"})
        
        # Create test user
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "auth_provider": "email",
            "hashed_password": get_password_hash("testpassword123"),
            "is_active": True,
            "timezone": "UTC",
            "currency": "USD"
        }
        
        result = await db.users.insert_one(user_data)
        user_id = result.inserted_id
        
        yield {"id": str(user_id), "email": "test@example.com", "password": "testpassword123"}
        
        # Cleanup
        await db.users.delete_one({"_id": ObjectId(user_id)})
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI"""
        return TestClient(app)
    
    def test_user_registration_success(self, client):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "newpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["auth_provider"] == "email"
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password
    
    def test_user_registration_duplicate_email(self, client):
        """Test registration with duplicate email fails"""
        # First registration
        client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "full_name": "First User",
            "password": "password123"
        })
        
        # Second registration with same email
        response = client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "full_name": "Second User",
            "password": "password456"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_user_login_success(self, client, test_user):
        """Test successful user login"""
        response = client.post("/api/v1/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user["email"]
    
    def test_user_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials fails"""
        response = client.post("/api/v1/auth/login", json={
            "email": test_user["email"],
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_get_current_user_profile(self, client, test_user):
        """Test getting current user profile with valid token"""
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        token = login_response.json()["access_token"]
        
        # Get profile
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["full_name"] == "Test User"
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting profile without token fails"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_refresh_token(self, client, test_user):
        """Test token refresh functionality"""
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        original_token = login_response.json()["access_token"]
        
        # Refresh token
        response = client.post("/api/v1/auth/refresh", headers={
            "Authorization": f"Bearer {original_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # New token should be different
        assert data["access_token"] != original_token


class TestIteration1CSVIngestion:
    """Test CSV upload, processing, and import functionality"""
    
    @pytest.fixture
    async def authenticated_user(self):
        """Create authenticated user for CSV tests"""
        db = get_database()
        
        # Clean up any existing test user
        await db.users.delete_many({"email": "csvtest@example.com"})
        
        # Create test user
        user_data = {
            "email": "csvtest@example.com",
            "full_name": "CSV Test User",
            "auth_provider": "email",
            "hashed_password": get_password_hash("csvtest123"),
            "is_active": True,
            "timezone": "UTC",
            "currency": "USD"
        }
        
        result = await db.users.insert_one(user_data)
        user_id = result.inserted_id
        
        yield {"id": str(user_id), "email": "csvtest@example.com", "password": "csvtest123"}
        
        # Cleanup
        await db.users.delete_one({"_id": ObjectId(user_id)})
    
    @pytest.fixture
    def auth_headers(self, client, authenticated_user):
        """Get authentication headers for API calls"""
        login_response = client.post("/api/v1/auth/login", json={
            "email": authenticated_user["email"],
            "password": authenticated_user["password"]
        })
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def sample_csv_file(self):
        """Create a sample CSV file for testing"""
        csv_content = """Date,Description,Amount,Balance
01/15/2024,Coffee Shop,4.50,1000.00
01/15/2024,Gas Station,45.00,955.50
01/16/2024,Grocery Store,125.75,829.75
01/17/2024,Restaurant,32.00,797.75
01/18/2024,Salary Deposit,2000.00,2797.75"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            yield f.name
        
        os.unlink(f.name)
    
    @pytest.fixture
    def invalid_csv_file(self):
        """Create an invalid CSV file (wrong format)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a CSV file")
            f.flush()
            yield f.name
        
        os.unlink(f.name)
    
    def test_csv_upload_success(self, client, sample_csv_file, auth_headers):
        """Test successful CSV file upload"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post(
                "/api/v1/imports/upload",
                files={"file": ("test.csv", f, "text/csv")},
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.csv"
        assert data["status"] in ["pending", "processing", "preview_ready"]
        assert data["file_size"] > 0
    
    def test_csv_upload_invalid_file_type(self, client, invalid_csv_file, auth_headers):
        """Test CSV upload rejects non-CSV files"""
        with open(invalid_csv_file, 'rb') as f:
            response = client.post(
                "/api/v1/imports/upload",
                files={"file": ("test.txt", f, "text/plain")},
                headers=auth_headers
            )
        
        assert response.status_code == 400
        assert "csv files" in response.json()["detail"].lower()
    
    def test_csv_upload_unauthorized(self, client, sample_csv_file):
        """Test CSV upload without authentication fails"""
        with open(sample_csv_file, 'rb') as f:
            response = client.post(
                "/api/v1/imports/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 401
    
    def test_get_import_preview(self, client, sample_csv_file, auth_headers):
        """Test getting import preview after upload"""
        # Upload file first
        with open(sample_csv_file, 'rb') as f:
            upload_response = client.post(
                "/api/v1/imports/upload",
                files={"file": ("test.csv", f, "text/csv")},
                headers=auth_headers
            )
        
        import_id = upload_response.json()["id"]
        
        # Wait a moment for processing
        import time
        time.sleep(1)
        
        # Get preview
        response = client.get(f"/api/v1/imports/{import_id}/preview", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "preview_ready"
        assert "detected_columns" in data
        assert "preview_data" in data
        assert data["total_rows"] > 0
        
        # Check column detection
        detected = data["detected_columns"]
        assert "columns" in detected
        assert "detection_confidence" in detected
        assert detected["detection_confidence"] > 0.8
    
    def test_update_column_mapping(self, client, sample_csv_file, auth_headers):
        """Test updating column mapping"""
        # Upload file first
        with open(sample_csv_file, 'rb') as f:
            upload_response = client.post(
                "/api/v1/imports/upload",
                files={"file": ("test.csv", f, "text/csv")},
                headers=auth_headers
            )
        
        import_id = upload_response.json()["id"]
        
        # Wait for processing
        import time
        time.sleep(1)
        
        # Update column mapping
        response = client.put(
            f"/api/v1/imports/{import_id}/column-mapping",
            json={
                "date_column": "Date",
                "amount_column": "Amount",
                "description_column": "Description",
                "balance_column": "Balance"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "column_mapping" in data
        assert data["column_mapping"]["date_column"] == "Date"
    
    def test_confirm_import(self, client, sample_csv_file, auth_headers):
        """Test confirming import and creating transactions"""
        # Upload file first
        with open(sample_csv_file, 'rb') as f:
            upload_response = client.post(
                "/api/v1/imports/upload",
                files={"file": ("test.csv", f, "text/csv")},
                headers=auth_headers
            )
        
        import_id = upload_response.json()["id"]
        
        # Wait for processing
        import time
        time.sleep(2)
        
        # Confirm import
        response = client.post(f"/api/v1/imports/{import_id}/confirm", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["processed_rows"] > 0
        assert data["total_rows"] > 0
    
    def test_list_imports(self, client, sample_csv_file, auth_headers):
        """Test listing user's imports"""
        # Upload a file first
        with open(sample_csv_file, 'rb') as f:
            client.post(
                "/api/v1/imports/upload",
                files={"file": ("test.csv", f, "text/csv")},
                headers=auth_headers
            )
        
        # List imports
        response = client.get("/api/v1/imports", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "filename" in data[0]
        assert "status" in data[0]


class TestIteration1Transactions:
    """Test transaction CRUD operations"""
    
    @pytest.fixture
    async def transaction_user(self):
        """Create user with transactions for testing"""
        db = get_database()
        
        # Clean up any existing test user
        await db.users.delete_many({"email": "txn@example.com"})
        
        # Create test user
        user_data = {
            "email": "txn@example.com",
            "full_name": "Transaction User",
            "auth_provider": "email",
            "hashed_password": get_password_hash("txn123"),
            "is_active": True,
            "timezone": "UTC",
            "currency": "USD"
        }
        
        result = await db.users.insert_one(user_data)
        user_id = result.inserted_id
        
        yield {"id": str(user_id), "email": "txn@example.com", "password": "txn123"}
        
        # Cleanup
        await db.users.delete_one({"_id": ObjectId(user_id)})
    
    @pytest.fixture
    def txn_auth_headers(self, client, transaction_user):
        """Get authentication headers for transaction tests"""
        login_response = client.post("/api/v1/auth/login", json={
            "email": transaction_user["email"],
            "password": transaction_user["password"]
        })
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_transaction(self, client, txn_auth_headers):
        """Test creating a new transaction"""
        response = client.post("/api/v1/transactions", json={
            "transaction_date": "2024-01-15T10:00:00",
            "amount": 45.50,
            "description": "Test transaction",
            "category": "Test Category"
        }, headers=txn_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 45.50
        assert data["description"] == "test transaction"
        assert data["normalized_description"] == "test transaction"
        assert data["category"] == "Test Category"
    
    def test_list_transactions(self, client, txn_auth_headers):
        """Test listing transactions with pagination"""
        # Create a few transactions first
        for i in range(5):
            client.post("/api/v1/transactions", json={
                "transaction_date": f"2024-01-{15+i:02d}T10:00:00",
                "amount": float(i + 1),
                "description": f"Transaction {i+1}"
            }, headers=txn_auth_headers)
        
        # List transactions
        response = client.get("/api/v1/transactions", headers=txn_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["transactions"]) > 0
    
    def test_get_transaction(self, client, txn_auth_headers):
        """Test getting a specific transaction"""
        # Create a transaction
        create_response = client.post("/api/v1/transactions", json={
            "transaction_date": "2024-01-15T10:00:00",
            "amount": 25.00,
            "description": "Get test transaction"
        }, headers=txn_auth_headers)
        
        transaction_id = create_response.json()["id"]
        
        # Get the transaction
        response = client.get(f"/api/v1/transactions/{transaction_id}", headers=txn_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction_id
        assert data["amount"] == 25.00
    
    def test_update_transaction(self, client, txn_auth_headers):
        """Test updating a transaction"""
        # Create a transaction
        create_response = client.post("/api/v1/transactions", json={
            "transaction_date": "2024-01-15T10:00:00",
            "amount": 30.00,
            "description": "Original description"
        }, headers=txn_auth_headers)
        
        transaction_id = create_response.json()["id"]
        
        # Update the transaction
        response = client.put(f"/api/v1/transactions/{transaction_id}", json={
            "description": "Updated description",
            "category": "Updated Category"
        }, headers=txn_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["category"] == "Updated Category"
        assert data["amount"] == 30.00  # Should remain unchanged
    
    def test_delete_transaction(self, client, txn_auth_headers):
        """Test deleting a transaction"""
        # Create a transaction
        create_response = client.post("/api/v1/transactions", json={
            "transaction_date": "2024-01-15T10:00:00",
            "amount": 15.00,
            "description": "To be deleted"
        }, headers=txn_auth_headers)
        
        transaction_id = create_response.json()["id"]
        
        # Delete the transaction
        response = client.delete(f"/api/v1/transactions/{transaction_id}", headers=txn_auth_headers)
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()
        
        # Verify it's gone
        get_response = client.get(f"/api/v1/transactions/{transaction_id}", headers=txn_auth_headers)
        assert get_response.status_code == 404
    
    def test_transaction_filtering(self, client, txn_auth_headers):
        """Test filtering transactions by date and category"""
        # Create transactions with different dates and categories
        client.post("/api/v1/transactions", json={
            "transaction_date": "2024-01-15T10:00:00",
            "amount": 100.00,
            "description": "Revenue transaction",
            "category": "Revenue"
        }, headers=txn_auth_headers)
        
        client.post("/api/v1/transactions", json={
            "transaction_date": "2024-02-15T10:00:00",
            "amount": -50.00,
            "description": "Expense transaction",
            "category": "Expense"
        }, headers=txn_auth_headers)
        
        # Filter by date range
        response = client.get(
            "/api/v1/transactions?start_date=2024-01-01&end_date=2024-01-31",
            headers=txn_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should only include January transactions
        assert all(
            datetime.fromisoformat(txn["transaction_date"].replace('Z', '+00:00')).month == 1
            for txn in data["transactions"]
        )


class TestIteration1Dashboard:
    """Test dashboard analytics and KPI endpoints"""
    
    @pytest.fixture
    async def dashboard_user(self):
        """Create user with transaction data for dashboard tests"""
        db = get_database()
        
        # Clean up any existing test user
        await db.users.delete_many({"email": "dash@example.com"})
        await db.transactions.delete_many({"user_id": ObjectId()})
        
        # Create test user
        user_data = {
            "email": "dash@example.com",
            "full_name": "Dashboard User",
            "auth_provider": "email",
            "hashed_password": get_password_hash("dash123"),
            "is_active": True,
            "timezone": "UTC",
            "currency": "USD"
        }
        
        result = await db.users.insert_one(user_data)
        user_id = result.inserted_id
        
        # Create sample transactions
        current_month = datetime(2024, 1, 15)
        last_month = datetime(2023, 12, 15)
        
        transactions = [
            # Current month revenue
            {"user_id": user_id, "transaction_date": current_month, "amount": 2000.00, "description": "Salary", "normalized_description": "salary", "balance": 2000.00},
            {"user_id": user_id, "transaction_date": current_month, "amount": 500.00, "description": "Freelance", "normalized_description": "freelance", "balance": 2500.00},
            # Current month expenses
            {"user_id": user_id, "transaction_date": current_month, "amount": -1200.00, "description": "Rent", "normalized_description": "rent", "balance": 1300.00},
            {"user_id": user_id, "transaction_date": current_month, "amount": -300.00, "description": "Groceries", "normalized_description": "groceries", "balance": 1000.00},
            # Last month data
            {"user_id": user_id, "transaction_date": last_month, "amount": 1800.00, "description": "Salary", "normalized_description": "salary", "balance": 1800.00},
            {"user_id": user_id, "transaction_date": last_month, "amount": -1000.00, "description": "Rent", "normalized_description": "rent", "balance": 800.00},
        ]
        
        await db.transactions.insert_many(transactions)
        
        yield {"id": str(user_id), "email": "dash@example.com", "password": "dash123"}
        
        # Cleanup
        await db.users.delete_one({"_id": ObjectId(user_id)})
        await db.transactions.delete_many({"user_id": user_id})
    
    @pytest.fixture
    def dash_auth_headers(self, client, dashboard_user):
        """Get authentication headers for dashboard tests"""
        login_response = client.post("/api/v1/auth/login", json={
            "email": dashboard_user["email"],
            "password": dashboard_user["password"]
        })
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_dashboard_overview(self, client, dash_auth_headers):
        """Test dashboard overview KPIs"""
        response = client.get("/api/v1/dashboard/overview", headers=dash_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = [
            "current_cash_balance", "total_revenue_this_month", "total_expenses_this_month",
            "net_income_this_month", "total_revenue_last_month", "total_expenses_last_month",
            "net_income_last_month", "revenue_change_percent", "expense_change_percent"
        ]
        
        for field in required_fields:
            assert field in data
            assert isinstance(data[field], (int, float))
        
        # Verify calculations
        # Current month: 2000 + 500 revenue, 1200 + 300 expenses = 2500 revenue, 1500 expenses, 1000 net
        assert data["total_revenue_this_month"] == 2500.0
        assert data["total_expenses_this_month"] == 1500.0
        assert data["net_income_this_month"] == 1000.0
        
        # Last month: 1800 revenue, 1000 expenses, 800 net
        assert data["total_revenue_last_month"] == 1800.0
        assert data["total_expenses_last_month"] == 1000.0
        assert data["net_income_last_month"] == 800.0
    
    def test_top_customers(self, client, dash_auth_headers):
        """Test top customers endpoint"""
        response = client.get("/api/v1/dashboard/top-customers", headers=dash_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should return revenue transactions (positive amounts)
        for customer in data:
            assert "id" in customer
            assert "name" in customer
            assert "entity_type" in customer
            assert "total_amount" in customer
            assert "transaction_count" in customer
            assert customer["total_amount"] > 0
    
    def test_top_suppliers(self, client, dash_auth_headers):
        """Test top suppliers endpoint"""
        response = client.get("/api/v1/dashboard/top-suppliers", headers=dash_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should return expense transactions (negative amounts converted to positive)
        for supplier in data:
            assert "id" in supplier
            assert "name" in supplier
            assert "entity_type" in supplier
            assert "total_amount" in supplier
            assert "transaction_count" in supplier
            assert supplier["total_amount"] > 0
    
    def test_monthly_trend(self, client, dash_auth_headers):
        """Test monthly trend data"""
        response = client.get("/api/v1/dashboard/monthly-trend?months=6", headers=dash_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "trend" in data
        assert isinstance(data["trend"], list)
        
        # Check trend data structure
        for month_data in data["trend"]:
            assert "month" in month_data
            assert "year" in month_data
            assert "month_number" in month_data
            assert "revenue" in month_data
            assert "expenses" in month_data
            assert "net_income" in month_data
            assert isinstance(month_data["revenue"], (int, float))
            assert isinstance(month_data["expenses"], (int, float))
            assert isinstance(month_data["net_income"], (int, float))


class TestIteration1Integration:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    async def integration_user(self):
        """Create user for integration tests"""
        db = get_database()
        
        # Clean up any existing test user
        await db.users.delete_many({"email": "integration@example.com"})
        
        # Create test user
        user_data = {
            "email": "integration@example.com",
            "full_name": "Integration User",
            "auth_provider": "email",
            "hashed_password": get_password_hash("integration123"),
            "is_active": True,
            "timezone": "UTC",
            "currency": "USD"
        }
        
        result = await db.users.insert_one(user_data)
        user_id = result.inserted_id
        
        yield {"id": str(user_id), "email": "integration@example.com", "password": "integration123"}
        
        # Cleanup
        await db.users.delete_one({"_id": ObjectId(user_id)})
    
    @pytest.fixture
    def integration_auth_headers(self, client, integration_user):
        """Get authentication headers for integration tests"""
        login_response = client.post("/api/v1/auth/login", json={
            "email": integration_user["email"],
            "password": integration_user["password"]
        })
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_complete_csv_workflow(self, client, integration_auth_headers):
        """Test complete CSV import workflow: upload -> preview -> confirm -> dashboard"""
        # Create sample CSV
        csv_content = """Date,Description,Amount,Balance
02/01/2024,Client Payment,1500.00,3000.00
02/02/2024,Office Supplies,-75.50,2924.50
02/03/2024,Software Subscription,-49.00,2875.50
02/04/2024,Consulting Fee,800.00,3675.50"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_file = f.name
        
        try:
            # Step 1: Upload CSV
            with open(csv_file, 'rb') as f:
                upload_response = client.post(
                    "/api/v1/imports/upload",
                    files={"file": ("integration_test.csv", f, "text/csv")},
                    headers=integration_auth_headers
                )
            
            assert upload_response.status_code == 200
            import_id = upload_response.json()["id"]
            
            # Step 2: Wait for processing and get preview
            import time
            time.sleep(2)
            
            preview_response = client.get(
                f"/api/v1/imports/{import_id}/preview",
                headers=integration_auth_headers
            )
            
            assert preview_response.status_code == 200
            preview_data = preview_response.json()
            assert preview_data["status"] == "preview_ready"
            assert preview_data["total_rows"] == 4
            
            # Step 3: Confirm import
            confirm_response = client.post(
                f"/api/v1/imports/{import_id}/confirm",
                headers=integration_auth_headers
            )
            
            assert confirm_response.status_code == 200
            confirm_data = confirm_response.json()
            assert confirm_data["status"] == "confirmed"
            assert confirm_data["processed_rows"] == 4
            
            # Step 4: Verify transactions were created
            transactions_response = client.get(
                "/api/v1/transactions",
                headers=integration_auth_headers
            )
            
            assert transactions_response.status_code == 200
            transactions = transactions_response.json()["transactions"]
            assert len(transactions) >= 4
            
            # Step 5: Check dashboard reflects new data
            dashboard_response = client.get(
                "/api/v1/dashboard/overview",
                headers=integration_auth_headers
            )
            
            assert dashboard_response.status_code == 200
            dashboard_data = dashboard_response.json()
            assert dashboard_data["total_revenue_this_month"] > 0
            assert dashboard_data["total_expenses_this_month"] < 0
            
        finally:
            os.unlink(csv_file)
    
    def test_error_handling_workflow(self, client, integration_auth_headers):
        """Test error handling throughout the application"""
        # Test unauthorized access
        response = client.get("/api/v1/transactions")
        assert response.status_code == 401
        
        # Test invalid transaction data
        response = client.post("/api/v1/transactions", json={
            "transaction_date": "invalid-date",
            "amount": "not-a-number",
            "description": ""
        }, headers=integration_auth_headers)
        
        # Should return validation error
        assert response.status_code == 422
        
        # Test non-existent resource
        response = client.get(
            "/api/v1/transactions/507f1f77bcf86cd799439011",
            headers=integration_auth_headers
        )
        assert response.status_code == 404


# Performance and Load Tests
class TestIteration1Performance:
    """Performance tests for Iteration 1 functionality"""
    
    @pytest.fixture
    async def performance_user(self):
        """Create user for performance tests"""
        db = get_database()
        
        await db.users.delete_many({"email": "perf@example.com"})
        
        user_data = {
            "email": "perf@example.com",
            "full_name": "Performance User",
            "auth_provider": "email",
            "hashed_password": get_password_hash("perf123"),
            "is_active": True,
            "timezone": "UTC",
            "currency": "USD"
        }
        
        result = await db.users.insert_one(user_data)
        user_id = result.inserted_id
        
        yield {"id": str(user_id), "email": "perf@example.com", "password": "perf123"}
        
        await db.users.delete_one({"_id": ObjectId(user_id)})
    
    @pytest.fixture
    def perf_auth_headers(self, client, performance_user):
        """Get authentication headers for performance tests"""
        login_response = client.post("/api/v1/auth/login", json={
            "email": performance_user["email"],
            "password": performance_user["password"]
        })
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_api_response_times(self, client, perf_auth_headers):
        """Test that API endpoints respond within acceptable time limits"""
        import time
        
        # Test health endpoint
        start_time = time.time()
        response = client.get("/health")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.1  # Should be under 100ms
        
        # Test authentication endpoint
        start_time = time.time()
        response = client.get("/api/v1/auth/me", headers=perf_auth_headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Should be under 500ms
        
        # Test dashboard endpoint
        start_time = time.time()
        response = client.get("/api/v1/dashboard/overview", headers=perf_auth_headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should be under 1 second


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
