import requests
import json

# Test login
login_url = "http://127.0.0.1:8000/api/v1/auth/login"
login_data = {
    "email": "test@example.com",
    "password": "test"
}

try:
    response = requests.post(login_url, json=login_data)
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        print(f"Login successful! Token: {token[:50]}...")
        
        # Test dashboard with authentication
        headers = {"Authorization": f"Bearer {token}"}
        dashboard_url = "http://127.0.0.1:8000/api/v1/dashboard/overview"
        
        response = requests.get(dashboard_url, headers=headers)
        print(f"Dashboard Status: {response.status_code}")
        print(f"Dashboard Response: {response.text}")
        
        # Test CSV import endpoint
        imports_url = "http://127.0.0.1:8000/api/v1/imports/"
        response = requests.get(imports_url, headers=headers)
        print(f"Imports Status: {response.status_code}")
        print(f"Imports Response: {response.text}")
        
    else:
        print(f"Login failed: {response.text}")
except Exception as e:
    print(f"Error: {e}")
