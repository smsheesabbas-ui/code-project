from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: Optional[str] = None
    messages: List[ChatMessage] = []
    context: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    initial_message: Optional[str] = None


class ChatMessageCreate(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ChatIntent(str, Enum):
    REVENUE_QUERY = "revenue_query"
    EXPENSE_QUERY = "expense_query"
    TOP_CUSTOMER_QUERY = "top_customer_query"
    TOP_SUPPLIER_QUERY = "top_supplier_query"
    CASHFLOW_QUERY = "cashflow_query"
    TREND_QUERY = "trend_query"
    FORECAST_QUERY = "forecast_query"
    COMPARISON_QUERY = "comparison_query"
    ENTITY_BREAKDOWN = "entity_breakdown"
    GENERAL_QUERY = "general_query"


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    content: str
    intent: Optional[ChatIntent] = None
    confidence: Optional[float] = None
    data_sources: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatSessionSummary(BaseModel):
    id: str
    title: Optional[str]
    message_count: int
    last_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
