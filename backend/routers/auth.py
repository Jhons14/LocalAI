"""
Authentication endpoints for user registration, login, and token management.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from database.base import get_db
from database.models import User
from services.auth import AuthService, JWTService
from services.security import get_current_active_user, get_optional_user
from config.settings import get_settings

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


# Request/Response Models
class UserRegistration(BaseModel):
    """User registration request model."""
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    password: str = Field(..., min_length=8, max_length=128, description="Password (8-128 characters)")


class UserLogin(BaseModel):
    """User login request model."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class TokenRefresh(BaseModel):
    """Token refresh request model."""
    refresh_token: str = Field(..., description="Valid refresh token")


class PasswordChange(BaseModel):
    """Password change request model."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


class AuthResponse(BaseModel):
    """Authentication response model."""
    user_id: str
    email: str
    username: str
    is_admin: bool
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    """Token refresh response model."""
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    """User profile response model."""
    user_id: str
    email: str
    username: str
    is_admin: bool
    is_active: bool
    created_at: str
    last_login: str = None


def get_auth_service() -> AuthService:
    """Get authentication service instance."""
    settings = get_settings()
    jwt_service = JWTService(settings)
    return AuthService(settings, jwt_service)


@router.post("/register", response_model=AuthResponse)
async def register_user(
    user_data: UserRegistration,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (will be unique in system)
    - **username**: Username (3-50 characters, will be unique in system)
    - **password**: Strong password (8-128 characters with complexity requirements)
    
    Returns authentication tokens upon successful registration.
    """
    success, message, user_response = auth_service.register_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return AuthResponse(**user_response)


@router.post("/login", response_model=AuthResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user with email and password.
    
    - **email**: Registered email address
    - **password**: User's password
    
    Returns authentication tokens upon successful login.
    Account will be locked after 5 failed attempts.
    """
    success, message, user_response = auth_service.authenticate_user(
        db=db,
        email=login_data.email,
        password=login_data.password
    )
    
    if not success:
        if "locked" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
    
    return AuthResponse(**user_response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    token_data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using a valid refresh token.
    
    - **refresh_token**: Valid refresh token obtained from login/register
    
    Returns new access token if refresh token is valid.
    """
    success, message, new_access_token = auth_service.refresh_token(token_data.refresh_token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    return TokenResponse(access_token=new_access_token)


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile information.
    
    Requires valid authentication token.
    """
    return UserProfile(
        user_id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_admin=current_user.is_admin,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
        last_login=current_user.last_login.isoformat() if current_user.last_login else None
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change user's password.
    
    - **current_password**: Current password for verification
    - **new_password**: New strong password
    
    Requires valid authentication token.
    """
    success, message = auth_service.change_password(
        db=db,
        user_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user.
    
    Note: With JWT tokens, logout is handled client-side by discarding tokens.
    This endpoint serves as a confirmation and for potential future token blacklisting.
    """
    return {"message": "Logged out successfully"}


@router.get("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify if current token is valid and get basic user info.
    
    Useful for client-side token validation.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_admin": current_user.is_admin
    }