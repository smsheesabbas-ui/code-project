#!/usr/bin/env python3
"""
Upload sample CSV data to production backend
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def upload_sample_csv():
    """Upload sample transactions CSV"""
    try:
        # Read the sample CSV file
        with open("backend/test_data/sample_transactions.csv", "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/imports/upload", files=files)
        
        print(f"Upload Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Upload Result: {result}")
            return result.get("id")
        else:
            print(f"Upload Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Upload failed: {e}")
        return None

def confirm_import(import_id):
    """Confirm the import to process transactions"""
    try:
        response = requests.post(f"{BASE_URL}/imports/{import_id}/confirm")
        print(f"Confirm Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Confirm Result: {result}")
            return True
        else:
            print(f"Confirm Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Confirm failed: {e}")
        return False

def test_intelligence():
    """Test intelligence endpoints"""
    try:
        # Test weekly summary
        response = requests.get(f"{BASE_URL}/intelligence/weekly-summary")
        print(f"Weekly Summary Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Summary: {data.get('summary', 'No summary')}")
        
        # Test recommendations
        response = requests.get(f"{BASE_URL}/intelligence/recommendations")
        print(f"Recommendations Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            print(f"Recommendations: {len(recommendations)} found")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. {rec}")
        
        # Test alerts
        response = requests.get(f"{BASE_URL}/intelligence/alerts")
        print(f"Alerts Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            print(f"Alerts: {len(alerts)} found")
        
        # Test forecast
        response = requests.get(f"{BASE_URL}/intelligence/forecasts/cashflow?days=30")
        print(f"Forecast Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Forecast Status: {data.get('status', 'Unknown')}")
            if data.get('status') == 'success':
                forecast = data.get('forecast', {})
                summary = forecast.get('summary', {})
                print(f"Total Predicted: ${summary.get('total_predicted', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"Intelligence test failed: {e}")
        return False

if __name__ == "__main__":
    print("Uploading sample data to production backend...")
    
    # Upload CSV
    import_id = upload_sample_csv()
    
    if import_id:
        print(f"Import ID: {import_id}")
        
        # Confirm import
        if confirm_import(import_id):
            print("Import confirmed successfully!")
            
            # Wait a moment for processing
            import time
            time.sleep(2)
            
            # Test intelligence features
            print("\nTesting intelligence features...")
            test_intelligence()
        else:
            print("Failed to confirm import")
    else:
        print("Failed to upload CSV")
    
    print("\nDone!")
