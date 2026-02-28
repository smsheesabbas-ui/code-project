from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId, MongoBaseModel


class Category(MongoBaseModel):
    user_id: PyObjectId
    name: str
    category_type: Literal["revenue", "expense"]
    is_default: bool = False
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CategoryCreate(BaseModel):
    name: str
    category_type: Literal["revenue", "expense"]
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    category_type: Optional[Literal["revenue", "expense"]] = None
    description: Optional[str] = None


class CategoryResponse(BaseModel):
    id: str
    user_id: str
    name: str
    category_type: str
    is_default: bool
    description: Optional[str]
    created_at: datetime
