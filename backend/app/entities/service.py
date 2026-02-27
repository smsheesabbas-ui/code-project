import uuid
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from datetime import datetime
from ..database import entities, transactions
from ..models.entity import EntityCreate, Entity, EntityUpdate, EntityCorrection
from ..ai.groq_client import get_groq_client


class EntityService:
    def __init__(self):
        self.groq_client = get_groq_client()
    
    async def create_entity(self, entity_data: EntityCreate, user_id: str) -> Entity:
        """Create a new entity manually"""
        # Check if entity already exists
        existing = await entities.find_one({
            "user_id": user_id,
            "normalized_name": entity_data.normalized_name.lower().strip()
        })
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Entity with this name already exists"
            )
        
        # Create entity
        entity_dict = entity_data.dict()
        entity_dict.update({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "total_revenue": 0.0,
            "total_expenses": 0.0,
            "transaction_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        await entities.insert_one(entity_dict)
        
        return Entity(**entity_dict)
    
    async def get_entities(self, user_id: str, entity_type: Optional[str] = None) -> List[Entity]:
        """Get all entities for user"""
        query = {"user_id": user_id}
        if entity_type:
            query["type"] = entity_type
        
        cursor = entities.find(query).sort("name", 1)
        entity_list = []
        async for doc in cursor:
            entity_list.append(Entity(**doc))
        
        return entity_list
    
    async def get_entity(self, entity_id: str, user_id: str) -> Entity:
        """Get specific entity"""
        entity = await entities.find_one({"id": entity_id, "user_id": user_id})
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entity not found"
            )
        
        return Entity(**entity)
    
    async def update_entity(self, entity_id: str, user_id: str, update_data: EntityUpdate) -> Entity:
        """Update entity"""
        entity = await entities.find_one({"id": entity_id, "user_id": user_id})
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entity not found"
            )
        
        # Update normalized name if name changed
        update_dict = update_data.dict(exclude_unset=True)
        if "name" in update_dict:
            update_dict["normalized_name"] = update_dict["name"].lower().strip()
        
        update_dict["updated_at"] = datetime.utcnow()
        
        await entities.update_one(
            {"id": entity_id},
            {"$set": update_dict}
        )
        
        updated_entity = await entities.find_one({"id": entity_id})
        return Entity(**updated_entity)
    
    async def delete_entity(self, entity_id: str, user_id: str) -> bool:
        """Delete entity (and update related transactions)"""
        entity = await entities.find_one({"id": entity_id, "user_id": user_id})
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entity not found"
            )
        
        # Remove entity reference from transactions
        await transactions.update_many(
            {"entity_id": entity_id, "user_id": user_id},
            {"$unset": {"entity_id": "", "entity_name": ""}}
        )
        
        # Delete entity
        await entities.delete_one({"id": entity_id})
        
        return True
    
    async def get_top_customers(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top customers by revenue"""
        pipeline = [
            {"$match": {"user_id": user_id, "amount": {"$gt": 0}}},
            {"$group": {
                "_id": "$entity_id",
                "total_revenue": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "entity_name": {"$first": "$entity_name"}
            }},
            {"$match": {"total_revenue": {"$gt": 0}}},
            {"$sort": {"total_revenue": -1}},
            {"$limit": limit}
        ]
        
        results = []
        cursor = transactions.aggregate(pipeline)
        async for doc in cursor:
            if doc["_id"]:  # Exclude transactions without entities
                results.append({
                    "entity_id": doc["_id"],
                    "entity_name": doc["entity_name"],
                    "total_revenue": doc["total_revenue"],
                    "transaction_count": doc["transaction_count"]
                })
        
        return results
    
    async def get_top_suppliers(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top suppliers by expenses"""
        pipeline = [
            {"$match": {"user_id": user_id, "amount": {"$lt": 0}}},
            {"$group": {
                "_id": "$entity_id",
                "total_expenses": {"$sum": {"$abs": "$amount"}},
                "transaction_count": {"$sum": 1},
                "entity_name": {"$first": "$entity_name"}
            }},
            {"$match": {"total_expenses": {"$gt": 0}}},
            {"$sort": {"total_expenses": -1}},
            {"$limit": limit}
        ]
        
        results = []
        cursor = transactions.aggregate(pipeline)
        async for doc in cursor:
            if doc["_id"]:  # Exclude transactions without entities
                results.append({
                    "entity_id": doc["_id"],
                    "entity_name": doc["entity_name"],
                    "total_expenses": doc["total_expenses"],
                    "transaction_count": doc["transaction_count"]
                })
        
        return results
    
    async def log_entity_correction(self, correction: EntityCorrection, user_id: str) -> bool:
        """Log entity correction for learning"""
        # Get the transaction
        transaction = await transactions.find_one({
            "id": correction.transaction_id,
            "user_id": user_id
        })
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Find or create the correct entity
        normalized_name = correction.correct_entity_name.lower().strip()
        entity = await entities.find_one({
            "user_id": user_id,
            "normalized_name": normalized_name
        })
        
        if not entity:
            # Create new entity
            entity_dict = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": correction.correct_entity_name,
                "normalized_name": normalized_name,
                "type": correction.correct_entity_type,
                "total_revenue": 0.0,
                "total_expenses": 0.0,
                "transaction_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await entities.insert_one(entity_dict)
            entity = entity_dict
        
        # Update transaction
        await transactions.update_one(
            {"id": correction.transaction_id},
            {"$set": {
                "entity_id": entity["id"],
                "entity_name": correction.correct_entity_name,
                "entity_corrected": True,
                "original_entity_id": correction.original_entity_id,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Update entity counters
        await self._update_entity_counters(entity["id"], user_id)
        
        return True
    
    async def _update_entity_counters(self, entity_id: str, user_id: str):
        """Update entity counters based on transactions"""
        pipeline = [
            {"$match": {"user_id": user_id, "entity_id": entity_id}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                "total_expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "transaction_count": {"$sum": 1},
                "last_transaction": {"$max": "$transaction_date"}
            }}
        ]
        
        result = await transactions.aggregate(pipeline).to_list(length=1)
        
        if result:
            totals = result[0]
            await entities.update_one(
                {"id": entity_id},
                {"$set": {
                    "total_revenue": totals["total_revenue"],
                    "total_expenses": totals["total_expenses"],
                    "transaction_count": totals["transaction_count"],
                    "last_transaction_date": totals["last_transaction"],
                    "updated_at": datetime.utcnow()
                }}
            )
    
    async def get_entity_insights(self, entity_id: str, user_id: str) -> Dict[str, Any]:
        """Get detailed insights for an entity"""
        entity = await self.get_entity(entity_id, user_id)
        
        # Get transaction trends
        pipeline = [
            {"$match": {"user_id": user_id, "entity_id": entity_id}},
            {"$group": {
                "_id": {"$dateTrunc": {"date": "$transaction_date", "unit": "month"}},
                "monthly_revenue": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
                "monthly_expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, {"$abs": "$amount"}, 0]}},
                "transaction_count": {"$sum": 1}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 12}
        ]
        
        monthly_data = []
        cursor = transactions.aggregate(pipeline)
        async for doc in cursor:
            monthly_data.append({
                "month": doc["_id"],
                "revenue": doc["monthly_revenue"],
                "expenses": doc["monthly_expenses"],
                "transaction_count": doc["transaction_count"]
            })
        
        return {
            "entity": entity,
            "monthly_trends": monthly_data,
            "total_transactions": entity.transaction_count,
            "average_transaction_value": (entity.total_revenue + entity.total_expenses) / max(entity.transaction_count, 1)
        }


entity_service = EntityService()
