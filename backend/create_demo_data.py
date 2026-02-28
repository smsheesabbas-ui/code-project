#!/usr/bin/env python3
"""
Create demo transaction data for the demo user
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
import random
from decimal import Decimal

# MongoDB connection
MONGO_URL = "mongodb://admin:password@localhost:27017/cashflow?authSource=admin"

# Sample transaction data
SAMPLE_TRANSACTIONS = [
    {"description": "Salary Deposit", "amount": 5000.00, "type": "Revenue", "category": "Salary", "entity_name": "Company ABC"},
    {"description": "Client Payment - Project X", "amount": 2500.00, "type": "Revenue", "category": "Consulting", "entity_name": "Client Corp"},
    {"description": "Office Rent", "amount": -1500.00, "type": "Expense", "category": "Rent", "entity_name": "Landlord LLC"},
    {"description": "Software Licenses", "amount": -299.00, "type": "Expense", "category": "Software", "entity_name": "Adobe Inc"},
    {"description": "Internet Bill", "amount": -89.99, "type": "Expense", "category": "Utilities", "entity_name": "ISP Provider"},
    {"description": "Coffee Shop", "amount": -15.50, "type": "Expense", "category": "Food", "entity_name": "Starbucks"},
    {"description": "Gas Station", "amount": -65.00, "type": "Expense", "category": "Transportation", "entity_name": "Shell Gas"},
    {"description": "Grocery Store", "amount": -234.67, "type": "Expense", "category": "Food", "entity_name": "Walmart"},
    {"description": "Insurance Premium", "amount": -450.00, "type": "Expense", "category": "Insurance", "entity_name": "State Farm"},
    {"description": "Freelance Project", "amount": 1200.00, "type": "Revenue", "category": "Freelance", "entity_name": "Freelance Client"},
]

def create_demo_data():
    """Create demo transaction data"""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URL)
        db = client.cashflow
        
        # Demo user ID
        DEMO_USER_ID = "69a235b64db7304c81b42977"
        
        # Clear existing demo data
        result = db.transactions.delete_many({"user_id": DEMO_USER_ID})
        print(f"Cleared {result.deleted_count} existing demo transactions")
        
        # Generate transactions for the last 90 days
        transactions = []
        base_date = datetime.utcnow() - timedelta(days=90)
        
        for day_offset in range(90):
            current_date = base_date + timedelta(days=day_offset)
            
            # Add 2-4 transactions per day
            num_transactions = random.randint(2, 4)
            
            for i in range(num_transactions):
                template = random.choice(SAMPLE_TRANSACTIONS)
                
                # Add some variation to amounts
                amount_variation = random.uniform(0.8, 1.2)
                amount = float(template["amount"]) * amount_variation
                
                transaction = {
                    "user_id": DEMO_USER_ID,
                    "description": template["description"],
                    "amount": round(amount, 2),
                    "balance": 0.0,  # Will be calculated later
                    "type": template["type"],
                    "category": template["category"],
                    "entity_name": template["entity_name"],
                    "transaction_date": current_date,
                    "created_at": current_date,
                    "updated_at": current_date,
                    "import_id": f"demo_import_{day_offset}",
                    "confidence_score": random.uniform(0.85, 0.95)
                }
                
                transactions.append(transaction)
        
        # Sort by date and calculate running balance
        transactions.sort(key=lambda x: x["transaction_date"])
        running_balance = 10000.00  # Starting balance
        
        for transaction in transactions:
            running_balance += transaction["amount"]
            transaction["balance"] = round(running_balance, 2)
        
        # Insert transactions
        if transactions:
            result = db.transactions.insert_many(transactions)
            print(f"Created {len(result.inserted_ids)} demo transactions")
            
            # Print summary
            total_revenue = sum(t["amount"] for t in transactions if t["amount"] > 0)
            total_expenses = abs(sum(t["amount"] for t in transactions if t["amount"] < 0))
            
            print(f"\nDemo Data Summary:")
            print(f"Total Transactions: {len(transactions)}")
            print(f"Total Revenue: ${total_revenue:,.2f}")
            print(f"Total Expenses: ${total_expenses:,.2f}")
            print(f"Net Cashflow: ${(total_revenue - total_expenses):,.2f}")
            print(f"Final Balance: ${running_balance:,.2f}")
            print(f"Date Range: {transactions[0]['transaction_date'].strftime('%Y-%m-%d')} to {transactions[-1]['transaction_date'].strftime('%Y-%m-%d')}")
        
        client.close()
        print("\nDemo data created successfully!")
        
    except Exception as e:
        print(f"Error creating demo data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_demo_data()
