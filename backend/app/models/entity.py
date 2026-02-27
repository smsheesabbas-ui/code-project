from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class EntityBase(BaseModel):
    name: str
    normalized_name: str
    type: str  # "customer", "supplier", or "unknown"

class EntityCreate(EntityBase):
    pass

class EntityUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None

class Entity(EntityBase):
    id: str
    user_id: str
    total_revenue: Decimal = Decimal('0')
    total_expenses: Decimal = Decimal('0')
    transaction_count: int = 0
    last_transaction_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class EntityInDB(Entity):
    class Config:
        from_attributes = True

class EntitySummary(BaseModel):
    id: str
    name: str
    type: str
    total_amount: Decimal
    transaction_count: int

class EntityCorrection(BaseModel):
    original_entity_id: str
    correct_entity_name: str
    correct_entity_type: str
    transaction_id: str
