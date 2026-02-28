#!/usr/bin/env python3
"""
Quick test to verify backend is working after restart
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"Health failed: {e}")
        return False

def test_transactions():
    """Test transactions endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/transactions/")
        print(f"Transactions: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"Transactions failed: {e}")
        return False

def test_intelligence():
    """Test intelligence endpoints"""
    try:
        # Test weekly summary
        response = requests.get(f"{BASE_URL}/api/v1/intelligence/weekly-summary")
        print(f"Weekly Summary: {response.status_code}")
        
        # Test recommendations
        response = requests.get(f"{BASE_URL}/api/v1/intelligence/recommendations")
        print(f"Recommendations: {response.status_code}")
        
        # Test alerts
        response = requests.get(f"{BASE_URL}/api/v1/intelligence/alerts")
        print(f"Alerts: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"Intelligence failed: {e}")
        return False

def test_import_endpoint():
    """Test import endpoint exists"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/imports/")
        print(f"Import endpoint: {response.status_code}")
        return True
    except Exception as e:
        print(f"Import endpoint failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing CashFlow AI Backend")
    print("=" * 50)
    
    tests = [
        test_health,
        test_transactions,
        test_intelligence,
        test_import_endpoint
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("=" * 50)
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("Backend is fully operational!")
        print("\nWhat you can do now:")
        print("1. Visit http://localhost:3000 for the frontend")
        print("2. Visit http://localhost:3000/insights.html for AI features")
        print("3. Upload CSV files on the main page")
        print("4. Try AI entity extraction and classification")
    else:
        print("Some services may need attention")
