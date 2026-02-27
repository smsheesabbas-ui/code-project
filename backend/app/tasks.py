import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from celery import current_task
from .celery_app import celery_app
from .database import csv_imports, transactions, entities, users
from .ingestion.service import ingestion_service
from .models.csv_import import ImportStatus
from .models.transaction import Transaction
from .config import settings
import uuid


@celery_app.task(bind=True)
def process_csv_import(self, import_id: str, user_id: str):
    """Process CSV import in background"""
    try:
        # Update task status
        self.update_state(state="PROCESSING", meta={"status": "Starting CSV processing"})
        
        # Get import record
        import_record = asyncio.run(csv_imports.find_one({"id": import_id, "user_id": user_id}))
        if not import_record:
            raise ValueError(f"Import {import_id} not found")
        
        # Update status to processing
        asyncio.run(csv_imports.update_one(
            {"id": import_id},
            {"$set": {"status": ImportStatus.PROCESSING, "updated_at": datetime.utcnow()}}
        ))
        
        # Process CSV (this was previously sync)
        result = asyncio.run(ingestion_service.process_csv(import_id, user_id))
        
        # Trigger AI classification
        classify_transactions.delay(import_id, user_id)
        
        return {"status": "completed", "import_id": import_id}
        
    except Exception as e:
        # Update import status to failed
        asyncio.run(csv_imports.update_one(
            {"id": import_id},
            {"$set": {
                "status": ImportStatus.FAILED,
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }}
        ))
        raise


@celery_app.task(bind=True)
def classify_transactions(self, import_id: str, user_id: str):
    """Classify transactions with AI in background"""
    try:
        self.update_state(state="PROCESSING", meta={"status": "Starting AI classification"})
        
        # Get transactions for this import
        transaction_list = asyncio.run(_get_transactions_for_import(import_id, user_id))
        
        groq_client = get_groq_client()
        processed_count = 0
        
        for transaction in transaction_list:
            # Extract entity
            entity_name, entity_confidence = asyncio.run(
                groq_client.extract_entity(transaction["description"])
            )
            
            # Categorize transaction
            category, category_confidence = asyncio.run(
                groq_client.categorize_transaction(
                    transaction["description"], 
                    transaction["amount"]
                )
            )
            
            # Find or create entity
            entity = asyncio.run(_find_or_create_entity(
                user_id, entity_name, entity_confidence
            ))
            
            # Update transaction with AI classifications
            asyncio.run(transactions.update_one(
                {"id": transaction["id"]},
                {"$set": {
                    "entity_id": entity["id"] if entity else None,
                    "entity_name": entity_name,
                    "entity_confidence": entity_confidence,
                    "category": category,
                    "category_confidence": category_confidence,
                    "ai_processed": True,
                    "updated_at": datetime.utcnow()
                }}
            ))
            
            processed_count += 1
            
            # Update progress
            if processed_count % 10 == 0:
                progress = (processed_count / len(transaction_list)) * 100
                self.update_state(
                    state="PROCESSING",
                    meta={"status": f"Classified {processed_count}/{len(transaction_list)} transactions", "progress": progress}
                )
        
        # Update entity counters
        update_entity_counters.delay(user_id)
        
        return {"status": "completed", "processed_count": processed_count}
        
    except Exception as e:
        print(f"Error in classify_transactions: {e}")
        raise


@celery_app.task
def update_entity_counters(user_id: str):
    """Recalculate denormalized entity totals"""
    try:
        # Get all entities for user
        entity_list = asyncio.run(_get_entities_for_user(user_id))
        
        for entity in entity_list:
            # Calculate totals from transactions
            pipeline = [
                {"$match": {"user_id": user_id, "entity_id": entity["id"]}},
                {"$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                    "total_expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                    "transaction_count": {"$sum": 1},
                    "last_transaction": {"$max": "$transaction_date"}
                }}
            ]
            
            result = asyncio.run(transactions.aggregate(pipeline).to_list(length=1))
            
            if result:
                totals = result[0]
                asyncio.run(entities.update_one(
                    {"id": entity["id"]},
                    {"$set": {
                        "total_revenue": totals["total_revenue"],
                        "total_expenses": totals["total_expenses"],
                        "transaction_count": totals["transaction_count"],
                        "last_transaction_date": totals["last_transaction"],
                        "updated_at": datetime.utcnow()
                    }}
                ))
        
        return {"status": "completed", "updated_entities": len(entity_list)}
        
    except Exception as e:
        print(f"Error updating entity counters: {e}")
        raise


@celery_app.task
def check_alerts():
    """Check for alerts and create notifications"""
    try:
        # Get all active users
        user_list = asyncio.run(_get_active_users())
        
        for user in user_list:
            asyncio.run(_check_user_alerts(user["id"]))
        
        return {"status": "completed", "users_checked": len(user_list)}
        
    except Exception as e:
        print(f"Error checking alerts: {e}")
        raise


@celery_app.task
def send_weekly_summaries():
    """Send weekly summary emails"""
    try:
        # Get all users with email notifications enabled
        user_list = asyncio.run(_get_users_with_email_notifications())
        
        for user in user_list:
            asyncio.run(_send_user_weekly_summary(user["id"]))
        
        return {"status": "completed", "emails_sent": len(user_list)}
        
    except Exception as e:
        print(f"Error sending weekly summaries: {e}")
        raise


async def _find_or_create_entity(user_id: str, entity_name: str, confidence: float) -> Dict[str, Any]:
    """Find existing entity or create new one"""
    if entity_name == "Unknown" or confidence < 0.3:
        return None
    
    # Try exact match on normalized name
    normalized_name = entity_name.lower().strip()
    entity = await entities.find_one({
        "user_id": user_id,
        "normalized_name": normalized_name
    })
    
    if entity:
        return entity
    
    # Try fuzzy match (simplified - in production use MongoDB text search)
    fuzzy_matches = await entities.find({
        "user_id": user_id,
        "name": {"$regex": entity_name, "$options": "i"}
    }).to_list(5)
    
    if fuzzy_matches:
        # Return best match (simplified logic)
        return fuzzy_matches[0]
    
    # Create new entity
    new_entity = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": entity_name,
        "normalized_name": normalized_name,
        "type": "unknown",  # Will be determined by transaction patterns
        "total_revenue": 0.0,
        "total_expenses": 0.0,
        "transaction_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await entities.insert_one(new_entity)
    return new_entity


async def _check_user_alerts(user_id: str):
    """Check alerts for a specific user"""
    from .alerts.service import alert_service
    
    try:
        new_alerts = await alert_service.check_user_alerts(user_id)
        return new_alerts
    except Exception as e:
        print(f"Error checking alerts for user {user_id}: {e}")
        return []


async def _send_user_weekly_summary(user_id: str):
    """Send weekly summary to a specific user"""
    from .notifications.service import notification_service
    
    try:
        success = await notification_service.send_weekly_summary_to_user(user_id)
        return success
    except Exception as e:
        print(f"Error sending weekly summary to user {user_id}: {e}")
        return False


# Helper functions for async operations
async def _get_transactions_for_import(import_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Get transactions for a specific import"""
    cursor = transactions.find({"import_id": import_id, "user_id": user_id})
    transaction_list = []
    async for doc in cursor:
        transaction_list.append(doc)
    return transaction_list


async def _get_entities_for_user(user_id: str) -> List[Dict[str, Any]]:
    """Get all entities for a user"""
    cursor = entities.find({"user_id": user_id})
    entity_list = []
    async for doc in cursor:
        entity_list.append(doc)
    return entity_list


async def _get_active_users() -> List[Dict[str, Any]]:
    """Get all active users"""
    cursor = users.find({"is_active": True})
    user_list = []
    async for doc in cursor:
        user_list.append(doc)
    return user_list


async def _get_users_with_email_notifications() -> List[Dict[str, Any]]:
    """Get users with email notifications enabled"""
    cursor = users.find({
        "is_active": True,
        "notification_preferences.weekly_summary": True
    })
    user_list = []
    async for doc in cursor:
        user_list.append(doc)
    return user_list
