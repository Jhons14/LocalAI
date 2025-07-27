"""
Authentication router for user registration, login, and token management.
Provides secure endpoints for user authentication operations.
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database import get_db
from database.models import User
from auth.jwt_handler import JWTHandler
from auth.password import PasswordHandler
from auth.schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    PasswordReset, PasswordResetConfirm, RefreshToken
)
from auth.dependencies import get_current_active_user, get_jwt_handler
from config.settings import AppSettings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    settings: AppSettings = Depends(get_settings)
):
    """
    Register a new user account.
    
    Args:
        user_data: User registration data
        request: FastAPI request object
        db: Database session
        settings: Application settings
        
    Returns:
        Created user information
        
    Raises:
        HTTPException: If email or username already exists
    """
    try:
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            logger.warning(f"Registration attempt with existing email: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already registered"
            )
        
        # Check if username already exists
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            logger.warning(f"Registration attempt with existing username: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Validate password strength
        password_handler = PasswordHandler()
        password_validation = password_handler.validate_password_strength(user_data.password)
        
        if not password_validation["is_valid"]:
            logger.warning(f"Weak password in registration: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet security requirements",
                    "feedback": password_validation["feedback"],
                    "score": password_validation["score"]
                }
            )
        
        # Hash password
        hashed_password = password_handler.hash_password(user_data.password)
        
        # Create new user
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            is_admin=False  # New users are not admins by default
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"New user registered: {new_user.email} from {_get_client_ip(request)}")
        
        return UserResponse.model_validate(new_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    settings: AppSettings = Depends(get_settings)
):
    """
    Authenticate user and return JWT tokens.
    
    Args:
        user_credentials: User login credentials
        request: FastAPI request object
        db: Database session
        jwt_handler: JWT handler instance
        settings: Application settings
        
    Returns:
        JWT access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Find user by email
        user = db.query(User).filter(User.email == user_credentials.email).first()
        if not user:
            logger.warning(f"Login attempt with non-existent email: {user_credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is locked
        if user.is_locked:
            logger.warning(f"Login attempt by locked user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts"
            )
        
        # Verify password
        password_handler = PasswordHandler()
        if not password_handler.verify_password(user_credentials.password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= settings.security.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=settings.security.lockout_duration_minutes
                )
                logger.warning(f"Account locked due to failed attempts: {user.email}")
            
            db.commit()
            
            logger.warning(f"Failed login attempt: {user.email} from {_get_client_ip(request)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt by inactive user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create JWT tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin
        }
        
        # Set token expiration based on remember_me option
        if user_credentials.remember_me:
            access_token_expires = timedelta(hours=24)  # Extended session
            refresh_token_expires = timedelta(days=30)
        else:
            access_token_expires = timedelta(minutes=settings.security.access_token_expire_minutes)
            refresh_token_expires = timedelta(days=7)
        
        access_token = jwt_handler.create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        refresh_token = jwt_handler.create_refresh_token(
            data=token_data,
            expires_delta=refresh_token_expires
        )
        
        logger.info(f"Successful login: {user.email} from {_get_client_ip(request)}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_data: RefreshToken,
    db: Session = Depends(get_db),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_data: Refresh token data
        db: Database session
        jwt_handler: JWT handler instance
        
    Returns:
        New JWT access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        # Verify refresh token
        payload = jwt_handler.verify_token(refresh_data.refresh_token, token_type="refresh")
        if payload is None:
            logger.warning("Invalid refresh token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user from database
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            logger.warning(f"Refresh attempt for invalid/inactive user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin
        }
        
        access_token = jwt_handler.create_access_token(data=token_data)
        new_refresh_token = jwt_handler.create_refresh_token(data=token_data)
        
        logger.info(f"Token refreshed for user: {user.email}")
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_active_user),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
):
    """
    Logout user by revoking tokens.
    
    Args:
        current_user: Current authenticated user
        jwt_handler: JWT handler instance
        
    Returns:
        Success message
    """
    # In a production system, you'd add the token to a blacklist
    # For now, we'll just log the logout
    logger.info(f"User logged out: {current_user.email}")
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return UserResponse.model_validate(current_user)


@router.post("/password-reset")
async def request_password_reset(
    reset_request: PasswordReset,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request password reset (send reset email).
    
    Args:
        reset_request: Password reset request data
        request: FastAPI request object
        db: Database session
        
    Returns:
        Success message (always, for security)
    """
    # Find user by email
    user = db.query(User).filter(User.email == reset_request.email).first()
    
    if user:
        # In a real system, you'd generate a secure token and send an email
        # For now, we'll just log the request
        logger.info(f"Password reset requested for: {user.email} from {_get_client_ip(request)}")
        
        # TODO: Generate reset token and send email
        # reset_token = secrets.token_urlsafe(32)
        # user.reset_token = reset_token
        # user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        # db.commit()
        # send_password_reset_email(user.email, reset_token)
    
    # Always return success message for security (don't leak email existence)
    return {"message": "If the email exists, a password reset link has been sent"}


def _get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    if request.client:
        return request.client.host
    
    return "unknown"