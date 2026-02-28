import asyncio
from celery import current_task
from celery.exceptions import Ignore
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.celery_app import celery_app
from app.core.database import get_database
from app.services.ai_service import ai_service
from app.services.forecasting_service import forecasting_service
from app.services.alert_service import alert_service


@celery_app.task(bind=True)
def process_csv_import(self, import_id: str) -> Dict:
    """Process CSV import in background"""
    try:
        # Update task status
        self.update_state(state='PROCESSING', meta={'status': 'Starting CSV processing'})
        
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_process_csv_import_async(import_id))
            return result
        finally:
            loop.close()
            
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Processing failed'}
        )
        raise


async def _process_csv_import_async(import_id: str) -> Dict:
    """Async CSV processing logic"""
    db = get_database()
    
    # Get import record
    import_record = await db.imports.find_one({"_id": import_id})
    if not import_record:
        raise ValueError(f"Import {import_id} not found")
    
    # Update status to processing
    await db.imports.update_one(
        {"_id": import_id},
        {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
    )
    
    # Process CSV (existing logic from imports.py)
    from app.services.csv_service import CSVProcessor
    csv_processor = CSVProcessor()
    
    # Read and process CSV file
    import pandas as pd
    df = pd.read_csv(f"/tmp/{import_id}.csv")
    
    # Detect columns
    detected_columns = csv_processor.detect_columns(df)
    total_rows = len(df)
    
    # Generate preview data
    preview_data = []
    for _, row in df.head(10).iterrows():
        preview_row = {}
        for col in df.columns:
            preview_row[col] = str(row[col]) if pd.notna(row[col]) else ""
        preview_data.append(preview_row)
    
    # Update import record
    await db.imports.update_one(
        {"_id": import_id},
        {"$set": {
            "status": "preview_ready",
            "total_rows": total_rows,
            "detected_columns": detected_columns,
            "preview_data": preview_data,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {
        "import_id": import_id,
        "status": "preview_ready",
        "total_rows": total_rows,
        "detected_columns": detected_columns
    }


@celery_app.task(bind=True)
def classify_transactions(self, import_id: str) -> Dict:
    """Classify transactions using AI"""
    try:
        self.update_state(state='PROCESSING', meta={'status': 'Starting AI classification'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_classify_transactions_async(import_id))
            return result
        finally:
            loop.close()
            
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Classification failed'}
        )
        raise


async def _classify_transactions_async(import_id: str) -> Dict:
    """Async transaction classification"""
    db = get_database()
    
    # Get transactions for this import
    transactions = await db.transactions.find({"import_id": import_id}).to_list(length=None)
    
    classified_count = 0
    for transaction in transactions:
        # Extract entity using AI
        entity_name = await ai_service.extract_entity(transaction["description"])
        
        # Classify category using AI
        category = await ai_service.classify_category(
            transaction["description"], 
            transaction["amount"]
        )
        
        # Update transaction with AI classifications
        update_data = {"updated_at": datetime.utcnow()}
        if entity_name:
            # Create or find entity
            entity = await _find_or_create_entity(
                transaction["user_id"], 
                entity_name
            )
            update_data["entity_id"] = entity["_id"]
            update_data["entity_name"] = entity["name"]
        
        if category:
            update_data["category"] = category
        
        await db.transactions.update_one(
            {"_id": transaction["_id"]},
            {"$set": update_data}
        )
        
        classified_count += 1
    
    return {
        "import_id": import_id,
        "classified_count": classified_count,
        "status": "completed"
    }


async def _find_or_create_entity(user_id: str, entity_name: str) -> Dict:
    """Find existing entity or create new one"""
    db = get_database()
    
    # Normalize name for matching
    normalized_name = entity_name.lower().strip()
    
    # Try exact match first
    entity = await db.entities.find_one({
        "user_id": user_id,
        "normalized_name": normalized_name
    })
    
    if entity:
        return entity
    
    # Create new entity
    new_entity = {
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
    
    result = await db.entities.insert_one(new_entity)
    new_entity["_id"] = result.inserted_id
    
    return new_entity


@celery_app.task
def update_cashflow_forecasts() -> Dict:
    """Update cashflow forecasts for all users"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_update_forecasts_async())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        return {"error": str(e), "status": "failed"}


async def _update_forecasts_async() -> Dict:
    """Update forecasts for all users"""
    db = get_database()
    
    # Get all active users
    users = await db.users.find({"is_active": True}).to_list(length=None)
    
    updated_count = 0
    for user in users:
        try:
            # Generate forecast
            forecast = await forecasting_service.generate_forecast(user["_id"])
            
            if forecast:
                # Save forecast
                forecast_data = {
                    "user_id": user["_id"],
                    "forecast_data": forecast,
                    "generated_at": datetime.utcnow(),
                    "forecast_period_days": 30
                }
                
                await db.forecasts.replace_one(
                    {"user_id": user["_id"]},
                    forecast_data,
                    upsert=True
                )
                
                updated_count += 1
                
        except Exception as e:
            print(f"Error generating forecast for user {user['_id']}: {e}")
    
    return {
        "updated_count": updated_count,
        "status": "completed"
    }


@celery_app.task
def check_financial_alerts() -> Dict:
    """Check and generate financial alerts"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_check_alerts_async())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        return {"error": str(e), "status": "failed"}


async def _check_alerts_async() -> Dict:
    """Check alerts for all users"""
    db = get_database()
    
    # Get all active users
    users = await db.users.find({"is_active": True}).to_list(length=None)
    
    alerts_generated = 0
    for user in users:
        try:
            # Check for alerts
            alerts = await alert_service.check_user_alerts(user["_id"])
            
            for alert in alerts:
                # Save alert
                alert_data = {
                    "user_id": user["_id"],
                    "alert_type": alert["type"],
                    "title": alert["title"],
                    "message": alert["message"],
                    "severity": alert["severity"],
                    "data": alert.get("data", {}),
                    "created_at": datetime.utcnow(),
                    "acknowledged": False
                }
                
                await db.alerts.insert_one(alert_data)
                alerts_generated += 1
                
        except Exception as e:
            print(f"Error checking alerts for user {user['_id']}: {e}")
    
    return {
        "alerts_generated": alerts_generated,
        "status": "completed"
    }


@celery_app.task
def generate_weekly_summaries() -> Dict:
    """Generate weekly AI summaries for all users"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_generate_summaries_async())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        return {"error": str(e), "status": "failed"}


async def _generate_summaries_async() -> Dict:
    """Generate weekly summaries for all users"""
    db = get_database()
    
    # Get all active users
    users = await db.users.find({"is_active": True}).to_list(length=None)
    
    summaries_generated = 0
    for user in users:
        try:
            # Get user's weekly data
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            # Aggregate weekly data
            pipeline = [
                {"$match": {
                    "user_id": user["_id"],
                    "transaction_date": {"$gte": week_ago}
                }},
                {"$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$cond": [{"$gte": ["$amount", 0]}, "$amount", 0]}},
                    "total_expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                    "transaction_count": {"$sum": 1},
                    "top_customer": {"$max": "$entity_name"},
                    "top_expense_category": {"$max": "$category"}
                }}
            ]
            
            result = await db.transactions.aggregate(pipeline).to_list(length=1)
            weekly_data = result[0] if result else {}
            
            # Generate AI summary
            summary = await ai_service.generate_weekly_summary(weekly_data)
            
            if summary:
                # Save summary
                summary_data = {
                    "user_id": user["_id"],
                    "summary": summary,
                    "data": weekly_data,
                    "period_start": week_ago,
                    "period_end": datetime.utcnow(),
                    "generated_at": datetime.utcnow()
                }
                
                await db.ai_insights.insert_one(summary_data)
                summaries_generated += 1
                
        except Exception as e:
            print(f"Error generating summary for user {user['_id']}: {e}")
    
    return {
        "summaries_generated": summaries_generated,
        "status": "completed"
    }
