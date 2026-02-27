from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from .config import settings
import redis.asyncio as redis

# MongoDB connection
client = AsyncIOMotorClient(settings.MONGODB_URL)
database = client.cashflow

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL)

# Collections
users = database.users
transactions = database.transactions
entities = database.entities
csv_imports = database.csv_imports
expense_categories = database.expense_categories
revenue_streams = database.revenue_streams
tags = database.tags
user_preferences = database.user_preferences

async def init_db():
    """Initialize database indexes"""
    try:
        # User indexes
        await users.create_index("email", unique=True)
        await users.create_index([("auth_provider", ASCENDING), ("auth_provider_id", ASCENDING)])
        
        # Transaction indexes
        await transactions.create_index([("user_id", ASCENDING), ("transaction_date", DESCENDING)])
        await transactions.create_index([("user_id", ASCENDING), ("entity_id", ASCENDING)])
        await transactions.create_index([("user_id", ASCENDING), ("import_id", ASCENDING)])
        
        # Entity indexes
        await entities.create_index([("user_id", ASCENDING), ("normalized_name", ASCENDING)], unique=True)
        
        # CSV Import indexes
        await csv_imports.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        
        # Category indexes
        await expense_categories.create_index([("user_id", ASCENDING), ("name", ASCENDING)], unique=True)
        await revenue_streams.create_index([("user_id", ASCENDING), ("name", ASCENDING)], unique=True)
        await tags.create_index([("user_id", ASCENDING), ("name", ASCENDING)], unique=True)
        
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Error creating database indexes: {e}")

async def get_db():
    """Get database instance"""
    return database

async def get_redis():
    """Get Redis instance"""
    return redis_client
