#!/usr/bin/env python3
"""
Simple test script for core functionality
Tests API endpoints without complex setup
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_health_endpoint():
    """Test health endpoint"""
    print("Testing health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        
        if response.status_code == 200:
            print("PASSED Health endpoint")
            print(f"   Response time: {response.elapsed.total_seconds()*1000:.0f}ms")
            return True
        else:
            print(f"FAILED Health endpoint - Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint: ERROR - {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\nTesting authentication endpoints...")
    
    # Test registration
    try:
        user_data = {
            "email": "testuser@example.com",
            "full_name": "Test User",
            "password": "testpass123"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        
        if response.status_code == 200:
            print("PASSED User registration")
        elif response.status_code == 400 and "already registered" in response.text:
            print("PASSED User registration (user already exists)")
        else:
            print(f"FAILED User registration - {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User registration: ERROR - {e}")
        return False
    
    # Test login with demo user
    try:
        login_data = {
            "email": "demo@cashflow.ai",
            "password": "demo123"
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        end_time = time.time()
        
        if response.status_code == 200:
            print("PASSED User login")
            print(f"   Response time: {(end_time - start_time)*1000:.0f}ms")
            
            # Test getting user profile
            token_data = response.json()
            token = token_data.get("access_token")
            
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                profile_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                
                if profile_response.status_code == 200:
                    print("PASSED User profile")
                else:
                    print(f"FAILED User profile - {profile_response.status_code}")
            else:
                print("FAILED User login - No token received")
                
        else:
            print(f"FAILED User login - {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User login: ERROR - {e}")
        return False

def test_dashboard_endpoint():
    """Test dashboard endpoint with authentication"""
    print("\nTesting dashboard endpoint...")
    
    try:
        # Login first
        login_data = {
            "email": "demo@cashflow.ai",
            "password": "demo123"
        }
        
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print("❌ Dashboard: FAILED - Cannot authenticate")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test dashboard
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/dashboard/overview", headers=headers)
        end_time = time.time()
        
        if response.status_code == 200:
            print("PASSED Dashboard endpoint")
            print(f"   Response time: {(end_time - start_time)*1000:.0f}ms")
            data = response.json()
            print(f"   Data keys: {list(data.keys())}")
            return True
        else:
            print(f"FAILED Dashboard endpoint - {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR Dashboard endpoint - {e}")
        return False

def test_transactions_endpoint():
    """Test transactions endpoint with authentication"""
    print("\nTesting transactions endpoint...")
    
    try:
        # Login first
        login_data = {
            "email": "demo@cashflow.ai",
            "password": "demo123"
        }
        
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print("❌ Transactions: FAILED - Cannot authenticate")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test transactions list
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/transactions", headers=headers)
        end_time = time.time()
        
        if response.status_code == 200:
            print("PASSED Transactions endpoint")
            print(f"   Response time: {(end_time - start_time)*1000:.0f}ms")
            data = response.json()
            if isinstance(data, dict) and 'transactions' in data:
                print(f"   Transactions count: {len(data['transactions'])}")
            return True
        else:
            print(f"FAILED Transactions endpoint - {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR Transactions endpoint - {e}")
        return False

def test_api_docs():
    """Test API documentation endpoint"""
    print("\nTesting API documentation...")
    
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/docs")
        
        if response.status_code == 200:
            print("PASSED API documentation")
            print(f"   Response time: {response.elapsed.total_seconds()*1000:.0f}ms")
            return True
        else:
            print(f"FAILED API documentation - {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR API documentation - {e}")
        return False

def main():
    """Run all simple tests"""
    print("CashFlow AI - Simple Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Authentication", test_auth_endpoints),
        ("Dashboard", test_dashboard_endpoint),
        ("Transactions", test_transactions_endpoint),
        ("API Documentation", test_api_docs)
    ]
    
    results = []
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, "PASSED" if success else "FAILED"))
        if success:
            passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, status in results:
        print(f"{status:<20} {test_name}")
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\nAll tests passed! Core functionality is working.")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed.")
        return 1

if __name__ == "__main__":
    exit(main())
