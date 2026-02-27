from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class TransactionBase(BaseModel):
    transaction_date: datetime
    description: str
    amount: Decimal
    currency: str = "USD"
    entity_id: Optional[str] = None
    category_id: Optional[str] = None
    tags: List[str] = []

class TransactionCreate(TransactionBase):
    import_id: Optional[str] = None

class TransactionUpdate(BaseModel):
    transaction_date: Optional[datetime] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    entity_id: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None

class Transaction(TransactionBase):
    id: str
    user_id: str
    import_id: Optional[str] = None
    import_timestamp: Optional[datetime] = None
    source_file_reference: Optional[str] = None
    is_duplicate: bool = False
    created_at: datetime
    updated_at: datetime

class TransactionInDB(Transaction):
    class Config:
        from_attributes = True

class TransactionList(BaseModel):
    transactions: List[Transaction]
    total: int
    page: int
    limit: int
