#!/usr/bin/env python3
"""
Create a test user using the API with short password
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def create_test_user():
    """Create test user via API"""
    
    # Test user data with short password
    user_data = {
        "email": "demo@cashflow.ai",
        "full_name": "Demo User",
        "password": "demo123"
    }
    
    print("Creating test user via API...")
    
    try:
        # Register the user
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        
        if response.status_code == 200:
            print("Test user created successfully!")
            print(f"   Email: {user_data['email']}")
            print(f"   Password: {user_data['password']}")
            print(f"   Full Name: {user_data['full_name']}")
            
            # Test login
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            
            login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if login_response.status_code == 200:
                login_result = login_response.json()
                print("   Login test: SUCCESS")
                print(f"   Token: {login_result['access_token'][:50]}...")
                
            else:
                print(f"   Login test: FAILED - {login_response.text}")
                
        elif response.status_code == 400 and "already registered" in response.text:
            print("Test user already exists!")
            print(f"   Email: {user_data['email']}")
            print(f"   Password: {user_data['password']}")
            
        else:
            print(f"Failed to create user: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to backend API")
        print("Make sure the backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Creating test user for CashFlow AI...")
    print()
    
    success = create_test_user()
    
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
