"""
Admin endpoints for system monitoring and management.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database.base import get_db
from database.models import User
from services.security import get_admin_user
from services.security.rate_limiting_middleware import EnhancedRateLimitMiddleware
from config.settings import get_settings

router = APIRouter(prefix="/admin", tags=["admin"])


# Response Models
class UserStatsResponse(BaseModel):
    """User statistics response model."""
    user_id: str
    email: str
    username: str
    is_active: bool
    total_requests: int = 0
    rate_limited_requests: int = 0
    current_limits: Dict = {}
    endpoints_used: Dict = {}


class SystemAnalyticsResponse(BaseModel):
    """System analytics response model."""
    total_requests: int
    rate_limited_requests: int
    rate_limit_percentage: float
    active_users: int
    endpoint_stats: Dict
    top_users: List[Dict]


class RateLimitConfigResponse(BaseModel):
    """Rate limit configuration response model."""
    chat_requests_per_minute: int
    key_operations_per_minute: int
    model_requests_per_minute: int
    max_login_attempts: int
    lockout_duration_minutes: int


# Request Models
class RateLimitResetRequest(BaseModel):
    """Rate limit reset request model."""
    user_id: str = Field(..., description="User ID to reset limits for")


class UserManagementRequest(BaseModel):
    """User management request model."""
    action: str = Field(..., description="Action: 'activate', 'deactivate', 'unlock'")
    user_id: str = Field(..., description="Target user ID")


@router.get("/analytics", response_model=SystemAnalyticsResponse)
async def get_system_analytics(
    request: Request,
    admin_user: User = Depends(get_admin_user)
):
    """
    Get system-wide rate limiting and usage analytics.
    
    Requires admin privileges.
    """
    # Get rate limiting middleware from app state
    rate_middleware = None
    
    # Find the rate limiting middleware in the app stack
    for middleware in request.app.middleware_stack:
        if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'EnhancedRateLimitMiddleware':
            rate_middleware = middleware.kwargs.get('middleware_instance')
            break
    
    if not rate_middleware:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting analytics not available"
        )
    
    analytics = rate_middleware.get_analytics()
    
    # Calculate top users by request count
    user_stats = analytics["analytics"]["user_stats"]
    top_users = sorted(
        [{"user_id": uid, **stats} for uid, stats in user_stats.items()],
        key=lambda x: x["total_requests"],
        reverse=True
    )[:10]
    
    return SystemAnalyticsResponse(
        total_requests=analytics["analytics"]["total_requests"],
        rate_limited_requests=analytics["analytics"]["rate_limited_requests"],
        rate_limit_percentage=analytics["rate_limit_percentage"],
        active_users=analytics["active_users"],
        endpoint_stats=analytics["analytics"]["endpoint_stats"],
        top_users=top_users
    )


@router.get("/users/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Get detailed statistics for a specific user.
    
    Requires admin privileges.
    """
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get rate limiting middleware
    rate_middleware = None
    for middleware in request.app.middleware_stack:
        if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'EnhancedRateLimitMiddleware':
            rate_middleware = middleware.kwargs.get('middleware_instance')
            break
    
    if not rate_middleware:
        # Return basic user info if middleware not available
        return UserStatsResponse(
            user_id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active
        )
    
    # Get detailed stats from middleware
    user_status = rate_middleware.get_user_rate_limit_status(user_id)
    
    return UserStatsResponse(
        user_id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        total_requests=user_status.get("total_requests", 0),
        rate_limited_requests=user_status.get("rate_limited_requests", 0),
        current_limits=user_status.get("current_limits", {}),
        endpoints_used=user_status.get("endpoints_used", {})
    )


@router.post("/rate-limits/reset")
async def reset_user_rate_limits(
    reset_request: RateLimitResetRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Reset rate limits for a specific user.
    
    Requires admin privileges.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == reset_request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get rate limiting middleware
    rate_middleware = None
    for middleware in request.app.middleware_stack:
        if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'EnhancedRateLimitMiddleware':
            rate_middleware = middleware.kwargs.get('middleware_instance')
            break
    
    if not rate_middleware:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service not available"
        )
    
    # Reset user's rate limits
    rate_middleware.rate_limiter.reset_user_limits(reset_request.user_id)
    
    return {"message": f"Rate limits reset for user {reset_request.user_id}"}


@router.get("/rate-limits/config", response_model=RateLimitConfigResponse)
async def get_rate_limit_config(
    admin_user: User = Depends(get_admin_user)
):
    """
    Get current rate limiting configuration.
    
    Requires admin privileges.
    """
    settings = get_settings()
    
    return RateLimitConfigResponse(
        chat_requests_per_minute=settings.rate_limit.chat_requests_per_minute,
        key_operations_per_minute=settings.rate_limit.key_operations_per_minute,
        model_requests_per_minute=settings.rate_limit.model_requests_per_minute,
        max_login_attempts=settings.security.max_login_attempts,
        lockout_duration_minutes=settings.security.lockout_duration_minutes
    )


@router.get("/users", response_model=List[UserStatsResponse])
async def list_all_users(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
    limit: int = 50,
    offset: int = 0
):
    """
    List all users with their basic stats.
    
    Requires admin privileges.
    """
    # Get users from database
    users = db.query(User).offset(offset).limit(limit).all()
    
    # Get rate limiting middleware
    rate_middleware = None
    for middleware in request.app.middleware_stack:
        if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'EnhancedRateLimitMiddleware':
            rate_middleware = middleware.kwargs.get('middleware_instance')
            break
    
    result = []
    for user in users:
        user_response = UserStatsResponse(
            user_id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active
        )
        
        # Add rate limiting stats if middleware available
        if rate_middleware:
            user_status = rate_middleware.get_user_rate_limit_status(user.id)
            if "error" not in user_status:
                user_response.total_requests = user_status.get("total_requests", 0)
                user_response.rate_limited_requests = user_status.get("rate_limited_requests", 0)
                user_response.current_limits = user_status.get("current_limits", {})
                user_response.endpoints_used = user_status.get("endpoints_used", {})
        
        result.append(user_response)
    
    return result


@router.post("/users/manage")
async def manage_user(
    management_request: UserManagementRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Manage user accounts (activate, deactivate, unlock).
    
    Requires admin privileges.
    """
    # Get target user
    user = db.query(User).filter(User.id == management_request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deactivating themselves
    if management_request.action == "deactivate" and user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own admin account"
        )
    
    try:
        if management_request.action == "activate":
            user.is_active = True
            message = f"User {user.username} activated"
            
        elif management_request.action == "deactivate":
            user.is_active = False
            message = f"User {user.username} deactivated"
            
        elif management_request.action == "unlock":
            user.failed_login_attempts = 0
            user.locked_until = None
            message = f"User {user.username} unlocked"
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Use 'activate', 'deactivate', or 'unlock'"
            )
        
        db.commit()
        
        return {"message": message}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to manage user: {str(e)}"
        )


@router.post("/analytics/reset")
async def reset_analytics(
    request: Request,
    admin_user: User = Depends(get_admin_user)
):
    """
    Reset all analytics data.
    
    Requires admin privileges.
    """
    # Get rate limiting middleware
    rate_middleware = None
    for middleware in request.app.middleware_stack:
        if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'EnhancedRateLimitMiddleware':
            rate_middleware = middleware.kwargs.get('middleware_instance')
            break
    
    if not rate_middleware:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service not available"
        )
    
    rate_middleware.reset_analytics()
    
    return {"message": "Analytics data reset successfully"}