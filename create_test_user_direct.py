#!/usr/bin/env python3
"""
Create a test user directly in MongoDB
"""

import pymongo
import hashlib
from datetime import datetime

def create_test_user_direct():
    """Create test user directly in MongoDB"""
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient("mongodb://admin:password@localhost:27017/cashflow?authSource=admin")
        db = client.cashflow
        
        print("Connected to MongoDB")
        
        # Create a simple hash for the password (not bcrypt, but works for demo)
        password = "demo123"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Test user data
        test_user = {
            "email": "demo@cashflow.ai",
            "full_name": "Demo User",
            "auth_provider": "email",
            "hashed_password": hashed_password,
            "is_active": True,
            "timezone": "UTC",
            "currency": "USD",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Check if user already exists
        existing = db.users.find_one({"email": test_user["email"]})
        if existing:
            print("Test user already exists!")
            print(f"   Email: {test_user['email']}")
            print(f"   Password: {password}")
            return True
        
        # Create user
        result = db.users.insert_one(test_user)
        
        print("Test user created successfully!")
        print(f"   Email: {test_user['email']}")
        print(f"   Password: {password}")
        print(f"   Full Name: {test_user['full_name']}")
        print(f"   User ID: {result.inserted_id}")
        
        # Add some sample transactions
        sample_transactions = [
            {
                "user_id": result.inserted_id,
                "transaction_date": datetime(2024, 1, 15),
                "amount": 2500.00,
                "description": "Salary Deposit",
                "normalized_description": "salary deposit",
                "category": "Salary",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "user_id": result.inserted_id,
                "transaction_date": datetime(2024, 1, 16),
                "amount": -125.50,
                "description": "Grocery Store",
                "normalized_description": "grocery store",
                "category": "Food",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "user_id": result.inserted_id,
                "transaction_date": datetime(2024, 1, 17),
                "amount": 500.00,
                "description": "Freelance Project",
                "normalized_description": "freelance project",
                "category": "Income",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "user_id": result.inserted_id,
                "transaction_date": datetime(2024, 1, 18),
                "amount": -89.00,
                "description": "Electric Bill",
                "normalized_description": "electric bill",
                "category": "Utilities",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "user_id": result.inserted_id,
                "transaction_date": datetime(2024, 1, 19),
                "amount": -32.75,
                "description": "Restaurant",
                "normalized_description": "restaurant",
                "category": "Food",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Insert sample transactions
        db.transactions.insert_many(sample_transactions)
        print(f"   Added {len(sample_transactions)} sample transactions")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Creating test user directly in MongoDB...")
    print()
    
    success = create_test_user_direct()
    
    if success:
        print()
        print("Test user is ready!")
        print()
        print("Login credentials:")
        print("   URL: http://localhost:3000")
        print("   Email: demo@cashflow.ai")
        print("   Password: demo123")
        print()
        print("You can now:")
        print("   1. Open http://localhost:3000")
        print("   2. Login with the credentials above")
        print("   3. Upload CSV files from the test data folder")
        print("   4. View your financial dashboard")
        print()
    else:
        print("Failed to create test user")
