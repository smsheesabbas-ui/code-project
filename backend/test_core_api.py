#!/usr/bin/env python3
"""
Core API functionality test
Tests basic endpoints without complex validation
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_basic_endpoints():
    """Test basic API functionality"""
    print("CashFlow AI - Core API Test")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Health endpoint
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   PASSED - Health endpoint responding")
            tests_passed += 1
        else:
            print(f"   FAILED - Status {response.status_code}")
    except Exception as e:
        print(f"   ERROR - {e}")
    tests_total += 1
    
    # Test 2: API docs
    print("\n2. Testing API Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("   PASSED - API documentation accessible")
            tests_passed += 1
        else:
            print(f"   FAILED - Status {response.status_code}")
    except Exception as e:
        print(f"   ERROR - {e}")
    tests_total += 1
    
    # Test 3: Authentication with demo user
    print("\n3. Testing Authentication...")
    try:
        # Login with demo user
        login_data = {
            "email": "demo@cashflow.ai",
            "password": "demo123"
        }
        
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data, timeout=5)
        
        if login_response.status_code == 200:
            print("   PASSED - Demo user login")
            tests_passed += 1
            
            # Test protected endpoint with token
            token = login_response.json().get("access_token")
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test dashboard endpoint
                dashboard_response = requests.get(f"{BASE_URL}/api/v1/dashboard/overview", headers=headers, timeout=5)
                if dashboard_response.status_code == 200:
                    print("   PASSED - Protected dashboard endpoint accessible")
                    tests_passed += 1
                else:
                    print(f"   FAILED - Dashboard status {dashboard_response.status_code}")
            else:
                print("   FAILED - No token received")
        else:
            print(f"   FAILED - Login status {login_response.status_code}")
            print(f"   Response: {login_response.text}")
    except Exception as e:
        print(f"   ERROR - {e}")
    tests_total += 1
    
    # Test 4: CSV upload endpoint
    print("\n4. Testing CSV Upload...")
    try:
        # First login to get token
        login_data = {
            "email": "demo@cashflow.ai",
            "password": "demo123"
        }
        
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data, timeout=5)
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test CSV upload
                csv_content = """Date,Description,Amount
01/15/2024,Test Transaction,100.00
01/16/2024,Another Test,-50.00"""
                
                files = {"file": ("test.csv", csv_content, "text/csv")}
                upload_response = requests.post(f"{BASE_URL}/api/v1/imports/upload", headers=headers, files=files, timeout=10)
                
                if upload_response.status_code in [200, 201]:
                    print("   PASSED - CSV upload endpoint accepting files")
                    tests_passed += 1
                else:
                    print(f"   FAILED - Upload status {upload_response.status_code}")
            else:
                print("   FAILED - No token for upload test")
        else:
            print("   FAILED - Cannot authenticate for upload test")
    except Exception as e:
        print(f"   ERROR - {e}")
    tests_total += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    success_rate = (tests_passed / tests_total) * 100 if tests_total > 0 else 0
    
    print(f"Total Tests: {tests_total}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_total - tests_passed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if tests_passed == tests_total:
        print("\nAll core API tests passed!")
        print("The CashFlow AI backend is functioning correctly.")
        return 0
    else:
        print(f"\n{tests_total - tests_passed} test(s) failed.")
        return 1

if __name__ == "__main__":
    exit(test_basic_endpoints())
