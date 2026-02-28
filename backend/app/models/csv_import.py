from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId, MongoBaseModel


class CSVImport(MongoBaseModel):
    user_id: PyObjectId
    filename: str
    file_path: str
    file_size: int
    status: Literal["pending", "processing", "preview_ready", "confirmed", "failed"]
    total_rows: int = 0
    processed_rows: int = 0
    duplicate_rows: int = 0
    error_rows: int = 0
    column_mapping: Optional[Dict[str, str]] = None
    detected_columns: Optional[Dict[str, Any]] = None
    preview_data: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ColumnMapping(BaseModel):
    date_column: Optional[str] = None
    amount_column: Optional[str] = None
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None
    description_column: Optional[str] = None
    balance_column: Optional[str] = None


class CSVImportResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    file_size: int
    status: str
    total_rows: int
    processed_rows: int
    duplicate_rows: int
    error_rows: int
    column_mapping: Optional[Dict[str, str]]
    detected_columns: Optional[Dict[str, Any]]
    preview_data: Optional[List[Dict[str, Any]]]
    error_message: Optional[str]
    created_at: datetime
