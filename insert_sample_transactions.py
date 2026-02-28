#!/usr/bin/env python3
"""
Insert sample transactions directly for testing
"""

import requests
from datetime import datetime, timedelta
import pymongo
from pymongo import MongoClient
from bson import ObjectId

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["cashflow"]

# Sample transactions
transactions = [
    {
        "user_id": "69a235b64db7304c81b42977",
        "date": "2024-01-01",
        "description": "Salary Deposit",
        "amount": 2500.00,
        "balance": 2500.00,
        "category": "Income",
        "entity_name": "Employer",
        "transaction_date": datetime(2024, 1, 1),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "user_id": "69a235b64db7304c81b42977",
        "date": "2024-01-02",
        "description": "Grocery Store",
        "amount": -125.50,
        "balance": 2374.50,
        "category": "Food",
        "entity_name": "Local Grocery",
        "transaction_date": datetime(2024, 1, 2),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "user_id": "69a235b64db7304c81b42977",
        "date": "2024-01-03",
        "description": "Gas Station",
        "amount": -45.00,
        "balance": 2329.50,
        "category": "Transport",
        "entity_name": "Shell Gas",
        "transaction_date": datetime(2024, 1, 3),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "user_id": "69a235b64db7304c81b42977",
        "date": "2024-01-04",
        "description": "Restaurant",
        "amount": -32.75,
        "balance": 2296.75,
        "category": "Food",
        "entity_name": "Local Restaurant",
        "transaction_date": datetime(2024, 1, 4),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "user_id": "69a235b64db7304c81b42977",
        "date": "2024-01-05",
        "description": "Freelance Project",
        "amount": 500.00,
        "balance": 2796.75,
        "category": "Income",
        "entity_name": "Freelance Client",
        "transaction_date": datetime(2024, 1, 5),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "user_id": "69a235b64db7304c81b42977",
        "date": "2024-01-06",
        "description": "Electric Bill",
        "amount": -89.00,
        "balance": 2707.75,
        "category": "Utilities",
        "entity_name": "Power Company",
        "transaction_date": datetime(2024, 1, 6),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "user_id": "69a235b64db7304c81b42977",
        "date": "2024-01-07",
        "description": "Coffee Shop",
        "amount": -4.50,
        "balance": 2712.25,
        "category": "Food",
        "entity_name": "Coffee Shop",
        "transaction_date": datetime(2024, 1, 7),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "user_id": "69a235b64db7304c81b42977",
        "date": "2024-01-08",
        "description": "Online Course",
        "amount": -99.00,
        "balance": 2613.25,
        "category": "Education",
        "entity_name": "Online Platform",
        "transaction_date": datetime(2024, 1, 8),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "user_id": "69a235b64db7304c81b42977",
        "date": "2024-01-09",
        "description": "Client Payment",
        "amount": 1200.00,
        "balance": 3813.25,
        "category": "Income",
        "entity_name": "Consulting Client",
        "transaction_date": datetime(2024, 1, 9),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "user_id": "69a235b64db7304c81b42977",
        "date": "2024-01-10",
        "description": "Internet Bill",
        "amount": -60.00,
        "balance": 3753.25,
        "category": "Utilities",
        "entity_name": "ISP Provider",
        "transaction_date": datetime(2024, 1, 10),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Add more transactions for better forecasting
for i in range(11, 32):  # January has 31 days
    date = datetime(2024, 1, i)
    if i % 7 == 0:  # Weekly income
        amount = 500.0 + (i % 3) * 200
        category = "Income"
        description = f"Weekly Payment {i}"
        entity_name = "Regular Client"
    elif i % 5 == 0:  # Monthly bills
        amount = -100.0 - (i % 4) * 50
        category = "Utilities"
        description = f"Monthly Bill {i}"
        entity_name = "Utility Company"
    else:  # Daily expenses
        amount = -20.0 - (i % 10) * 5
        category = ["Food", "Transport", "Office", "Personal"][i % 4]
        description = f"Daily Expense {i}"
        entity_name = f"Vendor {i % 5}"
    
    transactions.append({
        "user_id": "69a235b64db7304c81b42977",
        "date": date.strftime("%Y-%m-%d"),
        "description": description,
        "amount": amount,
        "balance": 3000.0 + (i * 10),  # Fake balance
        "category": category,
        "entity_name": entity_name,
        "transaction_date": date,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

# Clear existing transactions for demo user
db.transactions.delete_many({"user_id": "69a235b64db7304c81b42977"})

# Insert new transactions
result = db.transactions.insert_many(transactions)
print(f"Inserted {len(result.inserted_ids)} transactions")

# Test intelligence endpoints
BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(endpoint, name):
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"{name}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "summary" in data:
                print(f"  Summary: {data['summary'][:100]}...")
            elif "recommendations" in data:
                print(f"  Recommendations: {len(data['recommendations'])} found")
            elif "forecast" in data:
                print(f"  Forecast Status: {data.get('status', 'Unknown')}")
            elif "alerts" in data:
                print(f"  Alerts: {len(data['alerts'])} found")
        return response.status_code == 200
    except Exception as e:
        print(f"{name}: Error - {e}")
        return False

print("\nTesting intelligence endpoints:")
test_endpoint("/intelligence/weekly-summary", "Weekly Summary")
test_endpoint("/intelligence/recommendations", "Recommendations")
test_endpoint("/intelligence/forecasts/cashflow?days=30", "Forecast")
test_endpoint("/intelligence/alerts", "Alerts")

print("\nDone! Sample data is ready for testing insights.")
