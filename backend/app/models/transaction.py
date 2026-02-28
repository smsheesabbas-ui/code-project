from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId, MongoBaseModel


class Transaction(MongoBaseModel):
    user_id: PyObjectId
    transaction_date: datetime
    amount: float
    description: str
    normalized_description: str
    balance: Optional[float] = None
    entity_id: Optional[PyObjectId] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    import_id: Optional[PyObjectId] = None
    is_duplicate: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionCreate(BaseModel):
    transaction_date: datetime
    amount: float
    description: str
    balance: Optional[float] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class TransactionUpdate(BaseModel):
    transaction_date: Optional[datetime] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    balance: Optional[float] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    transaction_date: datetime
    amount: float
    description: str
    normalized_description: str
    balance: Optional[float]
    entity_id: Optional[str]
    category: Optional[str]
    tags: List[str]
    import_id: Optional[str]
    is_duplicate: bool
    created_at: datetime
