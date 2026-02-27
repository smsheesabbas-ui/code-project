from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .service import auth_service
from ..models.user import UserCreate, User, UserLogin, Token
from ..database import users
from ..config import settings
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# OAuth setup
oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

oauth.register(
    name='microsoft',
    client_id=settings.MICROSOFT_CLIENT_ID,
    client_secret=settings.MICROSOFT_CLIENT_SECRET,
    authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    payload = await auth_service.verify_token(token, "access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user = await users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return User(**user)

@router.post("/register", response_model=User)
async def register(user_data: UserCreate):
    user = await auth_service.create_user(user_data)
    return user

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await auth_service.authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.id})
    refresh_token = auth_service.create_refresh_token(data={"sub": user.id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = await auth_service.verify_token(token, "refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    access_token = auth_service.create_access_token(data={"sub": user_id})
    refresh_token = auth_service.create_refresh_token(data={"sub": user_id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/google")
async def google_login(request: Request):
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from Google"
        )
    
    # Create or get user
    from ..models.user import UserOAuthCreate, AuthProvider
    oauth_user_data = UserOAuthCreate(
        email=user_info['email'],
        full_name=user_info.get('name', ''),
        auth_provider=AuthProvider.GOOGLE,
        auth_provider_id=user_info['sub']
    )
    
    user = await auth_service.create_oauth_user(oauth_user_data)
    
    access_token = auth_service.create_access_token(data={"sub": user.id})
    refresh_token = auth_service.create_refresh_token(data={"sub": user.id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/microsoft")
async def microsoft_login(request: Request):
    redirect_uri = request.url_for('microsoft_callback')
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)

@router.get("/microsoft/callback")
async def microsoft_callback(request: Request):
    token = await oauth.microsoft.authorize_access_token(request)
    user_info = token.get('userinfo')
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from Microsoft"
        )
    
    # Create or get user
    from ..models.user import UserOAuthCreate, AuthProvider
    oauth_user_data = UserOAuthCreate(
        email=user_info['email'],
        full_name=user_info.get('name', ''),
        auth_provider=AuthProvider.MICROSOFT,
        auth_provider_id=user_info['sub']
    )
    
    user = await auth_service.create_oauth_user(oauth_user_data)
    
    access_token = auth_service.create_access_token(data={"sub": user.id})
    refresh_token = auth_service.create_refresh_token(data={"sub": user.id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # In a real implementation, you might want to invalidate the token
    # For now, we'll just return success
    return {"message": "Successfully logged out"}
