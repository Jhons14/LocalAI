"""
Authentication dependencies for FastAPI endpoints.
Provides secure user authentication and authorization.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from database.models import User
from auth.jwt_handler import JWTHandler
from auth.schemas import TokenData
from config.settings import AppSettings, get_settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


def get_jwt_handler(settings: AppSettings = Depends(get_settings)) -> JWTHandler:
    """Get JWT handler instance."""
    return JWTHandler(settings)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials
        db: Database session
        jwt_handler: JWT handler instance
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        logger.warning("No authorization credentials provided")
        raise credentials_exception
    
    try:
        # Verify and decode the token
        payload = jwt_handler.verify_token(credentials.credentials, token_type="access")
        if payload is None:
            logger.warning("Invalid or expired token")
            raise credentials_exception
        
        # Extract user information from token
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing user ID")
            raise credentials_exception
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.warning(f"User not found: {user_id}")
            raise credentials_exception
        
        # Log successful authentication
        logger.info(f"User authenticated: {user.email} from {_get_client_ip(request)}")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current authenticated and active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active User object
        
    Raises:
        HTTPException: If user is inactive or locked
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    if current_user.is_locked:
        logger.warning(f"Locked user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="User account is temporarily locked"
        )
    
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require admin privileges for endpoint access.
    
    Args:
        current_user: Current authenticated and active user
        
    Returns:
        Admin User object
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user attempted admin access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    
    return current_user


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that work with or without authentication.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials
        db: Database session
        jwt_handler: JWT handler instance
        
    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        # Try to get current user
        return await get_current_user(request, credentials, db, jwt_handler)
    except HTTPException:
        # If authentication fails, return None instead of raising exception
        return None


def require_scopes(*required_scopes: str):
    """
    Decorator factory for requiring specific scopes/permissions.
    
    Args:
        required_scopes: List of required permission scopes
        
    Returns:
        Dependency function that checks user scopes
    """
    async def check_scopes(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # For now, we'll use a simple admin check
        # In a more complex system, you'd implement proper scope checking
        user_scopes = ["admin"] if current_user.is_admin else ["user"]
        
        for scope in required_scopes:
            if scope not in user_scopes:
                logger.warning(
                    f"User {current_user.email} missing required scope: {scope}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {scope}"
                )
        
        return current_user
    
    return check_scopes


def _get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


class RateLimitExempt:
    """Dependency to mark endpoints as exempt from rate limiting."""
    
    def __init__(self, reason: str = "Authenticated user"):
        self.reason = reason
    
    def __call__(self, current_user: User = Depends(get_current_active_user)):
        # This dependency ensures user is authenticated and can be used
        # by rate limiting middleware to provide exemptions
        return current_user