#!/usr/bin/env python3
"""
Test Iteration 2 Intelligence Features
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_weekly_summary():
    """Test weekly summary endpoint"""
    print("Testing Weekly Summary...")
    
    try:
        response = requests.get(f"{BASE_URL}/intelligence/weekly-summary")
        print(f"Weekly Summary Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Summary: {data.get('summary', 'No summary')[:100]}...")
            print(f"Data Points: {data.get('data', {})}")
            return True
        else:
            print(f"Weekly Summary Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Weekly Summary Test Error: {e}")
        return False

def test_recommendations():
    """Test recommendations endpoint"""
    print("\nTesting Recommendations...")
    
    try:
        response = requests.get(f"{BASE_URL}/intelligence/recommendations")
        print(f"Recommendations Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            print(f"Recommendations Count: {len(recommendations)}")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. {rec}")
            return True
        else:
            print(f"Recommendations Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Recommendations Test Error: {e}")
        return False

def test_forecast():
    """Test cashflow forecast endpoint"""
    print("\nTesting Cashflow Forecast...")
    
    try:
        response = requests.get(f"{BASE_URL}/intelligence/forecasts/cashflow?days=30")
        print(f"Forecast Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Forecast Status: {data.get('status', 'Unknown')}")
            
            if data.get('status') == 'success':
                forecast = data.get('forecast', {})
                summary = forecast.get('summary', {})
                print(f"Total Predicted: ${summary.get('total_predicted', 0):.2f}")
                print(f"Average Daily: ${summary.get('average_daily', 0):.2f}")
                print(f"Trend: {summary.get('trend_direction', 'Unknown')}")
            else:
                print(f"Forecast Message: {data.get('message', 'No message')}")
            
            return True
        else:
            print(f"Forecast Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Forecast Test Error: {e}")
        return False

def test_alerts():
    """Test alerts endpoint"""
    print("\nTesting Alerts...")
    
    try:
        response = requests.get(f"{BASE_URL}/intelligence/alerts")
        print(f"Alerts Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            print(f"Alerts Count: {data.get('count', 0)}")
            
            for alert in alerts[:3]:
                print(f"  - {alert.get('title', 'No title')}: {alert.get('severity', 'unknown')}")
            
            return True
        else:
            print(f"Alerts Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Alerts Test Error: {e}")
        return False

def test_entity_extraction():
    """Test entity extraction endpoint"""
    print("\nTesting Entity Extraction...")
    
    try:
        test_description = "ACME CORP PAYMENT - INV#1234 FOR CONSULTING SERVICES"
        response = requests.post(
            f"{BASE_URL}/intelligence/extract-entity",
            json={"description": test_description}
        )
        print(f"Entity Extraction Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Description: {data.get('description')}")
            print(f"Extracted Entity: {data.get('extracted_entity')}")
            print(f"Confidence: {data.get('confidence')}")
            return True
        else:
            print(f"Entity Extraction Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Entity Extraction Test Error: {e}")
        return False

def test_category_classification():
    """Test category classification endpoint"""
    print("\nTesting Category Classification...")
    
    try:
        test_description = "Monthly software subscription for project management tools"
        response = requests.post(
            f"{BASE_URL}/intelligence/classify-category",
            json={"description": test_description, "amount": -49.99}
        )
        print(f"Category Classification Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Description: {data.get('description')}")
            print(f"Amount: ${data.get('amount')}")
            print(f"Classified Category: {data.get('classified_category')}")
            print(f"Confidence: {data.get('confidence')}")
            return True
        else:
            print(f"Category Classification Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Category Classification Test Error: {e}")
        return False

def test_alert_checking():
    """Test manual alert checking"""
    print("\nTesting Manual Alert Checking...")
    
    try:
        response = requests.post(f"{BASE_URL}/intelligence/alerts/check")
        print(f"Alert Check Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Alerts Found: {data.get('alerts_found', 0)}")
            print(f"Checked At: {data.get('checked_at')}")
            
            alerts = data.get('alerts', [])
            for alert in alerts:
                print(f"  - {alert.get('title')}: {alert.get('message')}")
            
            return True
        else:
            print(f"Alert Check Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Alert Check Test Error: {e}")
        return False

if __name__ == "__main__":
    print("CashFlow AI - Iteration 2 Intelligence Features Test")
    print("=" * 60)
    
    tests = [
        test_weekly_summary,
        test_recommendations,
        test_forecast,
        test_alerts,
        test_entity_extraction,
        test_category_classification,
        test_alert_checking
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All intelligence features are working!")
    else:
        print("⚠️  Some features may need configuration (GROQ_API_KEY)")
        print("Note: Some features work in demo mode without API keys")
