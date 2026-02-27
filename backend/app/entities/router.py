from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from ..service import entity_service
from ..models.entity import Entity, EntityCreate, EntityUpdate, EntityCorrection
from ..auth.router import get_current_user
from ..models.user import User

router = APIRouter(prefix="/entities", tags=["entities"])

@router.post("/", response_model=Entity)
async def create_entity(
    entity_data: EntityCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new entity"""
    return await entity_service.create_entity(entity_data, current_user.id)

@router.get("/", response_model=List[Entity])
async def get_entities(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    current_user: User = Depends(get_current_user)
):
    """Get all entities for user"""
    return await entity_service.get_entities(current_user.id, entity_type)

@router.get("/{entity_id}", response_model=Entity)
async def get_entity(
    entity_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific entity"""
    return await entity_service.get_entity(entity_id, current_user.id)

@router.put("/{entity_id}", response_model=Entity)
async def update_entity(
    entity_id: str,
    update_data: EntityUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update entity"""
    return await entity_service.update_entity(entity_id, current_user.id, update_data)

@router.delete("/{entity_id}")
async def delete_entity(
    entity_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete entity"""
    await entity_service.delete_entity(entity_id, current_user.id)
    return {"message": "Entity deleted successfully"}

@router.get("/top-customers", response_model=List[dict])
async def get_top_customers(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get top customers by revenue"""
    return await entity_service.get_top_customers(current_user.id, limit)

@router.get("/top-suppliers", response_model=List[dict])
async def get_top_suppliers(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get top suppliers by expenses"""
    return await entity_service.get_top_suppliers(current_user.id, limit)

@router.get("/{entity_id}/insights")
async def get_entity_insights(
    entity_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed insights for an entity"""
    return await entity_service.get_entity_insights(entity_id, current_user.id)

@router.post("/corrections")
async def log_entity_correction(
    correction: EntityCorrection,
    current_user: User = Depends(get_current_user)
):
    """Log entity correction for learning"""
    await entity_service.log_entity_correction(correction, current_user.id)
    return {"message": "Correction logged successfully"}
