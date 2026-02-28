#!/usr/bin/env python3
"""
Create a test user for CashFlow AI
Run this script to create a test account for login
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.auth import get_password_hash
from app.core.config import settings
from datetime import datetime

async def create_test_user():
    """Create a test user in the database"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client.get_database()
    
    try:
        # Test user data
        test_user = {
            "email": "demo@cashflow.ai",
            "full_name": "Demo User",
            "auth_provider": "email",
            "hashed_password": get_password_hash("demo123"),
            "is_active": True,
            "timezone": "UTC",
            "currency": "USD",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Check if user already exists
        existing = await database.users.find_one({"email": test_user["email"]})
        if existing:
            print(f"Test user already exists: {test_user['email']}")
            print(f"   Password: demo123")
            return
        
        # Create user
        result = await database.users.insert_one(test_user)
        
        print("Test user created successfully!")
        print(f"   Email: {test_user['email']}")
        print(f"   Password: demo123")
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
        await database.transactions.insert_many(sample_transactions)
        print(f"   Added {len(sample_transactions)} sample transactions")
        
    except Exception as e:
        print(f"Error creating test user: {e}")
        return False
    
    finally:
        client.close()
    
    return True

if __name__ == "__main__":
    print("Creating test user for CashFlow AI...")
    print()
    
    success = asyncio.run(create_test_user())
    
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
        sys.exit(1)
