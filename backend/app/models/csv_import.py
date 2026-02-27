from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ImportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PREVIEW_READY = "preview_ready"
    COMPLETED = "completed"
    FAILED = "failed"

class ColumnMapping(BaseModel):
    date: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None
    debit: Optional[str] = None
    credit: Optional[str] = None
    balance: Optional[str] = None

class CSVImportBase(BaseModel):
    filename: str
    file_size: int

class CSVImportCreate(CSVImportBase):
    pass

class CSVImport(CSVImportBase):
    id: str
    user_id: str
    status: ImportStatus
    column_mapping: Optional[ColumnMapping] = None
    detection_confidence: Optional[float] = None
    total_rows: Optional[int] = None
    processed_rows: Optional[int] = None
    duplicate_rows: Optional[int] = None
    error_rows: Optional[int] = None
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CSVImportInDB(CSVImport):
    class Config:
        from_attributes = True

class PreviewRow(BaseModel):
    row_number: int
    date: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    balance: Optional[float] = None
    is_duplicate: bool = False
    validation_errors: List[str] = []

class ImportPreview(BaseModel):
    import_id: str
    status: ImportStatus
    column_mapping: ColumnMapping
    detection_confidence: float
    rows: List[PreviewRow]
    total_rows: int
    validation_summary: Dict[str, int]
