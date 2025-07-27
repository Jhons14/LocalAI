"""
User management router for profile and account operations.
Provides endpoints for user profile management and admin operations.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from database.models import User, APIKey, ChatSession
from auth.schemas import UserResponse, UserUpdate, UserStats, APIKeyResponse
from auth.dependencies import get_current_active_user, require_admin
from auth.password import PasswordHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile information
    """
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.
    
    Args:
        user_update: Profile update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # If updating email, check it's not already taken
        if user_update.email and user_update.email != current_user.email:
            existing_email = db.query(User).filter(User.email == user_update.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address already in use"
                )
            current_user.email = user_update.email
        
        # Update full name if provided
        if user_update.full_name is not None:
            current_user.full_name = user_update.full_name
        
        # Handle password change
        if user_update.new_password:
            if not user_update.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password required to set new password"
                )
            
            # Verify current password
            password_handler = PasswordHandler()
            if not password_handler.verify_password(
                user_update.current_password, 
                current_user.hashed_password
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Validate new password strength
            password_validation = password_handler.validate_password_strength(user_update.new_password)
            if not password_validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "New password does not meet security requirements",
                        "feedback": password_validation["feedback"]
                    }
                )
            
            # Hash and update password
            current_user.hashed_password = password_handler.hash_password(user_update.new_password)
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Profile updated for user: {current_user.email}")
        return UserResponse.model_validate(current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's usage statistics.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User usage statistics
    """
    try:
        # Calculate statistics
        total_chat_sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).count()
        
        total_messages = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).with_entities(ChatSession.message_count).all()
        total_messages_count = sum(session[0] or 0 for session in total_messages)
        
        api_keys_count = db.query(APIKey).filter(
            APIKey.user_id == current_user.id,
            APIKey.is_active == True
        ).count()
        
        # Get last activity (most recent chat session activity)
        last_session = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).order_by(ChatSession.last_activity.desc()).first()
        
        last_activity = last_session.last_activity if last_session else None
        
        # Calculate account age
        from datetime import datetime
        account_age = (datetime.utcnow() - current_user.created_at).days
        
        return UserStats(
            total_chat_sessions=total_chat_sessions,
            total_messages=total_messages_count,
            api_keys_count=api_keys_count,
            last_activity=last_activity,
            account_age_days=account_age
        )
        
    except Exception as e:
        logger.error(f"Stats calculation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate user statistics"
        )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def get_user_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False, description="Include inactive API keys")
):
    """
    Get current user's API keys.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        include_inactive: Whether to include inactive keys
        
    Returns:
        List of user's API keys (without exposing actual key values)
    """
    query = db.query(APIKey).filter(APIKey.user_id == current_user.id)
    
    if not include_inactive:
        query = query.filter(APIKey.is_active == True)
    
    api_keys = query.order_by(APIKey.created_at.desc()).all()
    
    return [APIKeyResponse.model_validate(key) for key in api_keys]


@router.delete("/api-keys/{key_id}")
async def delete_user_api_key(
    key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user's API key.
    
    Args:
        key_id: API key ID to delete
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If key not found or unauthorized
    """
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    db.delete(api_key)
    db.commit()
    
    logger.info(f"API key deleted: {key_id} by user {current_user.email}")
    return {"message": "API key deleted successfully"}


# Admin-only endpoints
@router.get("/", response_model=List[UserResponse])
async def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    active_only: bool = Query(True, description="Return only active users")
):
    """
    List all users (admin only).
    
    Args:
        db: Database session
        current_user: Current authenticated admin user
        skip: Number of users to skip
        limit: Number of users to return
        active_only: Return only active users
        
    Returns:
        List of users
    """
    query = db.query(User)
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    users = query.offset(skip).limit(limit).all()
    
    return [UserResponse.model_validate(user) for user in users]


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user active status (admin only).
    
    Args:
        user_id: User ID to update
        is_active: New active status
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = is_active
    db.commit()
    
    logger.info(f"User status updated: {user.email} -> active={is_active} by {current_user.email}")
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}


@router.put("/{user_id}/admin")
async def update_user_admin_status(
    user_id: str,
    is_admin: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user admin status (admin only).
    
    Args:
        user_id: User ID to update
        is_admin: New admin status
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or trying to modify own admin status
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own admin status"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_admin = is_admin
    db.commit()
    
    logger.info(f"User admin status updated: {user.email} -> admin={is_admin} by {current_user.email}")
    return {"message": f"User admin status {'granted' if is_admin else 'revoked'} successfully"}