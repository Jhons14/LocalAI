"""
FastAPI security dependencies for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.base import get_db
from database.models import User
from services.auth import AuthService, JWTService
from config.settings import get_settings


# Security scheme for Bearer token
security = HTTPBearer()


def get_auth_service() -> AuthService:
    """Get authentication service instance."""
    settings = get_settings()
    jwt_service = JWTService(settings)
    return AuthService(settings, jwt_service)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        auth_service: Authentication service
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(db, token)
        
        if user is None:
            raise credentials_exception
            
        return user
        
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    if current_user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is locked"
        )
    
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to get current admin user.
    
    Args:
        current_user: Current active user
        
    Returns:
        Current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        db: Database session
        auth_service: Authentication service
        
    Returns:
        Current authenticated user or None
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(db, token)
        return user if user and user.is_active and not user.is_locked else None
    except Exception:
        return None