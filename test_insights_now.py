#!/usr/bin/env python3
"""
Test insights with current data
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_intelligence():
    """Test all intelligence endpoints"""
    print("Testing Intelligence Features")
    print("=" * 40)
    
    # Test weekly summary
    try:
        response = requests.get(f"{BASE_URL}/intelligence/weekly-summary")
        print(f"Weekly Summary: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Summary: {data.get('summary', 'No summary')[:100]}...")
            print(f"  Data Points: {data.get('data', {})}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"Weekly Summary Error: {e}")
    
    # Test recommendations
    try:
        response = requests.get(f"{BASE_URL}/intelligence/recommendations")
        print(f"Recommendations: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            print(f"  Recommendations: {len(recommendations)} found")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"    {i}. {rec}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"Recommendations Error: {e}")
    
    # Test alerts
    try:
        response = requests.get(f"{BASE_URL}/intelligence/alerts")
        print(f"Alerts: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            print(f"  Alerts: {len(alerts)} found")
            for alert in alerts[:3]:
                print(f"    - {alert.get('title', 'No title')}: {alert.get('severity', 'unknown')}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"Alerts Error: {e}")
    
    # Test forecast
    try:
        response = requests.get(f"{BASE_URL}/intelligence/forecasts/cashflow?days=30")
        print(f"Forecast: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Forecast Status: {data.get('status', 'Unknown')}")
            if data.get('status') == 'success':
                forecast = data.get('forecast', {})
                summary = forecast.get('summary', {})
                print(f"  Total Predicted: ${summary.get('total_predicted', 0):.2f}")
                print(f"  Average Daily: ${summary.get('average_daily', 0):.2f}")
                print(f"  Trend: {summary.get('trend_direction', 'Unknown')}")
                confidence = data.get('confidence_metrics', {}).get('overall_confidence', 0)
                print(f"  Confidence: {confidence:.1%}")
            else:
                print(f"  Message: {data.get('message', 'No message')}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"Forecast Error: {e}")
    
    # Test entity extraction
    try:
        response = requests.post(
            f"{BASE_URL}/intelligence/extract-entity",
            json={"description": "ACME CORP PAYMENT - INV#1234 FOR CONSULTING SERVICES"}
        )
        print(f"Entity Extraction: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Extracted Entity: {data.get('extracted_entity', 'None')}")
            print(f"  Confidence: {data.get('confidence', 'unknown')}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"Entity Extraction Error: {e}")
    
    # Test category classification
    try:
        response = requests.post(
            f"{BASE_URL}/intelligence/classify-category",
            json={"description": "Monthly software subscription for project management", "amount": -49.99}
        )
        print(f"Category Classification: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Classified Category: {data.get('classified_category', 'None')}")
            print(f"  Confidence: {data.get('confidence', 'unknown')}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"Category Classification Error: {e}")
    
    print("\n" + "=" * 40)
    print("Intelligence testing complete!")

if __name__ == "__main__":
    test_intelligence()
