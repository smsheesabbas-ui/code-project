#!/usr/bin/env python3
"""
Test CSV upload functionality
"""

import requests
import os

BASE_URL = "http://localhost:8000/api/v1"

def test_csv_upload():
    """Test CSV upload with sample file"""
    
    # Path to sample CSV
    csv_file_path = "test_data/sample_transactions.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found: {csv_file_path}")
        return False
    
    print(f"Testing CSV upload with: {csv_file_path}")
    
    try:
        # Upload CSV file
        with open(csv_file_path, 'rb') as f:
            files = {'file': ('test.csv', f, 'text/csv')}
            response = requests.post(f"{BASE_URL}/imports/upload", files=files)
        
        print(f"Upload Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Upload Response: {data}")
            
            import_id = data.get('id')
            if import_id:
                print(f"Import ID: {import_id}")
                
                # Try to get preview
                preview_response = requests.get(f"{BASE_URL}/imports/{import_id}/preview")
                print(f"Preview Status: {preview_response.status_code}")
                
                if preview_response.status_code == 200:
                    preview_data = preview_response.json()
                    print(f"Preview Data: {preview_data}")
                else:
                    print(f"Preview Error: {preview_response.text}")
            else:
                print("No import ID in response")
        else:
            print(f"Upload Error: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"Upload Test Error: {e}")
        return False

def test_transactions_endpoint():
    """Test transactions endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/transactions/")  # Add trailing slash
        print(f"Transactions Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Transactions Data Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            if 'transactions' in data:
                print(f"Found {len(data['transactions'])} transactions")
        else:
            print(f"Transactions Error: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"Transactions Test Error: {e}")
        return False

if __name__ == "__main__":
    print("CashFlow AI - CSV Upload Test")
    print("=" * 40)
    
    print("\n1. Testing Transactions Endpoint...")
    test_transactions_endpoint()
    
    print("\n2. Testing CSV Upload...")
    test_csv_upload()
