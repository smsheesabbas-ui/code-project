from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from app.core.config import settings
from typing import Optional


client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """Create database connection"""
    global client, database
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
        # Test the connection
        await client.admin.command('ping')
        database = client.get_database()
        
        # Create indexes
        await create_indexes()
        print("Connected to MongoDB")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        print("Continuing without database connection...")
        # Don't exit, just continue without database


async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")


async def create_indexes():
    """Create database indexes for performance"""
    try:
        # Transactions indexes
        await database.transactions.create_index([("user_id", ASCENDING), ("transaction_date", DESCENDING)])
        await database.transactions.create_index([("user_id", ASCENDING), ("entity_id", ASCENDING)])
        await database.transactions.create_index([("user_id", ASCENDING), ("import_id", ASCENDING)])
        
        # Entities indexes
        await database.entities.create_index([("user_id", ASCENDING), ("normalized_name", ASCENDING)], unique=True)
        
        # Users indexes
        await database.users.create_index("email", unique=True)
        
        # CSV imports indexes
        await database.csv_imports.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Failed to create indexes: {e}")
        # Continue without indexes


def get_database():
    """Get database instance"""
    return database
