from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from ..database import users
from ..models.user import UserCreate, UserOAuthCreate, UserInDB, AuthProvider
from ..config import settings
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def verify_token(self, token: str, token_type: str = "access") -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        user = await users.find_one({"email": email, "auth_provider": "email"})
        if not user:
            return None
        if not self.verify_password(password, user["hashed_password"]):
            return None
        return UserInDB(**user)

    async def create_user(self, user_data: UserCreate) -> UserInDB:
        # Check if user already exists
        existing_user = await users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        user_dict = user_data.dict()
        user_dict["id"] = str(uuid.uuid4())
        user_dict["auth_provider"] = AuthProvider.EMAIL
        user_dict["auth_provider_id"] = None
        user_dict["hashed_password"] = self.get_password_hash(user_data.password)
        user_dict["is_active"] = True
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()

        # Remove password from dict (we only store hashed password)
        del user_dict["password"]

        result = await users.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id

        return UserInDB(**user_dict)

    async def create_oauth_user(self, user_data: UserOAuthCreate) -> UserInDB:
        # Check if user already exists
        existing_user = await users.find_one({
            "auth_provider": user_data.auth_provider,
            "auth_provider_id": user_data.auth_provider_id
        })
        if existing_user:
            return UserInDB(**existing_user)

        # Create new OAuth user
        user_dict = user_data.dict()
        user_dict["id"] = str(uuid.uuid4())
        user_dict["hashed_password"] = None
        user_dict["is_active"] = True
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()

        result = await users.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id

        return UserInDB(**user_dict)

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        user = await users.find_one({"email": email})
        if user:
            return UserInDB(**user)
        return None

    async def get_user_by_oauth(self, provider: AuthProvider, provider_id: str) -> Optional[UserInDB]:
        user = await users.find_one({
            "auth_provider": provider,
            "auth_provider_id": provider_id
        })
        if user:
            return UserInDB(**user)
        return None

auth_service = AuthService()
