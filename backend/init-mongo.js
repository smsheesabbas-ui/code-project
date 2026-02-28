// MongoDB initialization script
// This script runs when MongoDB container starts for the first time

// Switch to cashflow database
db = db.getSiblingDB('cashflow');

// Create collections (they will be created automatically on first use)
// This ensures the database exists with proper structure

print('MongoDB initialization completed for CashFlow AI database');
print('Database: cashflow');
print('Collections will be created automatically on first use');

// Create initial indexes for better performance
// Note: These will also be created by the application on startup

print('MongoDB ready for connections');
