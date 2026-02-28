#!/usr/bin/env python3
"""
Quick test to upload sample data and test insights
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def create_sample_transactions():
    """Create some sample transactions directly via API"""
    
    # Sample transaction data
    sample_transactions = [
        {
            "date": "2024-01-01",
            "description": "Salary Deposit",
            "amount": 2500.00,
            "balance": 2500.00,
            "category": "Income",
            "entity_name": "Employer"
        },
        {
            "date": "2024-01-02", 
            "description": "Grocery Store",
            "amount": -125.50,
            "balance": 2374.50,
            "category": "Food",
            "entity_name": "Local Grocery"
        },
        {
            "date": "2024-01-03",
            "description": "Gas Station",
            "amount": -45.00,
            "balance": 2329.50,
            "category": "Transport",
            "entity_name": "Shell Gas"
        },
        {
            "date": "2024-01-04",
            "description": "Restaurant",
            "amount": -32.75,
            "balance": 2296.75,
            "category": "Food", 
            "entity_name": "Local Restaurant"
        },
        {
            "date": "2024-01-05",
            "description": "Freelance Project",
            "amount": 500.00,
            "balance": 2796.75,
            "category": "Income",
            "entity_name": "Freelance Client"
        }
    ]
    
    # Add more transactions for better insights
    for i in range(6, 31):  # Add transactions for the rest of January
        if i % 7 == 0:  # Weekly income
            sample_transactions.append({
                "date": f"2024-01-{i:02d}",
                "description": f"Weekly Payment {i}",
                "amount": 300.0 + (i % 3) * 100,
                "balance": 2500.0 + (i * 20),
                "category": "Income",
                "entity_name": "Regular Client"
            })
        elif i % 5 == 0:  # Monthly bills
            sample_transactions.append({
                "date": f"2024-01-{i:02d}",
                "description": f"Monthly Bill {i}",
                "amount": -80.0 - (i % 4) * 20,
                "balance": 2500.0 + (i * 20),
                "category": "Utilities",
                "entity_name": "Utility Company"
            })
        else:  # Daily expenses
            sample_transactions.append({
                "date": f"2024-01-{i:02d}",
                "description": f"Daily Expense {i}",
                "amount": -15.0 - (i % 8) * 3,
                "balance": 2500.0 + (i * 20),
                "category": ["Food", "Transport", "Office", "Personal"][i % 4],
                "entity_name": f"Vendor {i % 5}"
            })
    
    return sample_transactions

def test_insights_with_data():
    """Test insights after adding sample data"""
    
    print("Testing CashFlow AI with Sample Data")
    print("=" * 50)
    
    # Test current state
    print("\nCurrent Insights (before data):")
    try:
        response = requests.get(f"{BASE_URL}/intelligence/weekly-summary")
        if response.status_code == 200:
            data = response.json()
            print(f"  Summary: {data.get('summary', 'No summary')[:80]}...")
    except:
        print("  Error getting summary")
    
    # Create sample CSV content
    transactions = create_sample_transactions()
    
    # Create CSV content
    csv_content = "Date,Description,Amount,Balance,Category,Entity\n"
    for t in transactions:
        csv_content += f"{t['date']},{t['description']},{t['amount']},{t['balance']},{t['category']},{t['entity_name']}\n"
    
    # Upload CSV
    print(f"\nUploading {len(transactions)} sample transactions...")
    try:
        files = {'file': ('sample.csv', csv_content, 'text/csv')}
        response = requests.post(f"{BASE_URL}/imports/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            import_id = result.get('id')
            print(f"  Upload successful! Import ID: {import_id}")
            
            # Confirm import
            print("Processing import...")
            confirm_response = requests.post(f"{BASE_URL}/imports/{import_id}/confirm")
            
            if confirm_response.status_code == 200:
                print("  Import processed successfully!")
            else:
                print(f"  Import confirmation failed: {confirm_response.text}")
        else:
            print(f"  Upload failed: {response.text}")
            
    except Exception as e:
        print(f"  Upload error: {e}")
    
    # Wait a moment for processing
    import time
    time.sleep(2)
    
    # Test insights again
    print("\nInsights After Data Upload:")
    
    # Weekly summary
    try:
        response = requests.get(f"{BASE_URL}/intelligence/weekly-summary")
        if response.status_code == 200:
            data = response.json()
            print(f"  Weekly Summary: {data.get('summary', 'No summary')[:100]}...")
    except:
        print("  Error getting summary")
    
    # Recommendations
    try:
        response = requests.get(f"{BASE_URL}/intelligence/recommendations")
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            print(f"  Recommendations: {len(recommendations)} found")
            for i, rec in enumerate(recommendations[:2], 1):
                print(f"    {i}. {rec}")
    except:
        print("  Error getting recommendations")
    
    # Alerts
    try:
        response = requests.get(f"{BASE_URL}/intelligence/alerts")
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            print(f"  Alerts: {len(alerts)} found")
    except:
        print("  Error getting alerts")
    
    # Forecast
    try:
        response = requests.get(f"{BASE_URL}/intelligence/forecasts/cashflow?days=30")
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'Unknown')
            print(f"  Forecast Status: {status}")
            if status == 'success':
                forecast = data.get('forecast', {})
                summary = forecast.get('summary', {})
                print(f"    Total Predicted: ${summary.get('total_predicted', 0):.2f}")
            else:
                print(f"    Message: {data.get('message', 'No message')}")
    except:
        print("  Error getting forecast")
    
    print("\n" + "=" * 50)
    print("Test Complete!")
    print("\nNow you can:")
    print("1. Visit http://localhost:3000 for the main dashboard")
    print("2. Click 'Insights' in the navigation to see AI features")
    print("3. Try the entity extraction and classification tools")
    print("4. Upload your own CSV files for real insights")

if __name__ == "__main__":
    test_insights_with_data()
