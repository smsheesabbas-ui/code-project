from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId, MongoBaseModel


class Entity(MongoBaseModel):
    user_id: PyObjectId
    name: str
    normalized_name: str
    entity_type: Literal["customer", "supplier"]
    total_transactions: int = 0
    total_amount: float = 0.0
    last_transaction_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EntityCreate(BaseModel):
    name: str
    entity_type: Literal["customer", "supplier"]


class EntityUpdate(BaseModel):
    name: Optional[str] = None
    entity_type: Optional[Literal["customer", "supplier"]] = None


class EntityResponse(BaseModel):
    id: str
    user_id: str
    name: str
    normalized_name: str
    entity_type: str
    total_transactions: int
    total_amount: float
    last_transaction_date: Optional[datetime]
    created_at: datetime
