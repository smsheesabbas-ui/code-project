from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    MICROSOFT = "microsoft"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    timezone: str = "UTC"
    currency: str = "USD"

class UserCreate(UserBase):
    password: str

class UserOAuthCreate(UserBase):
    auth_provider: AuthProvider
    auth_provider_id: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None

class UserInDB(UserBase):
    id: str
    auth_provider: AuthProvider
    auth_provider_id: Optional[str] = None
    hashed_password: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class User(UserBase):
    id: str
    auth_provider: AuthProvider
    is_active: bool
    created_at: datetime

class UserInDBInternal(UserBase):
    id: str
    auth_provider: AuthProvider
    auth_provider_id: Optional[str] = None
    hashed_password: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
