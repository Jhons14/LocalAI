"""
Authentication middleware for JWT token validation and user context.
"""

import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from database.base import SessionLocal
from database.models import User
from services.auth import AuthService, JWTService
from services.security import UserRateLimiter
from config.settings import get_settings
import logging

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for handling JWT authentication and user context."""
    
    def __init__(self, app, settings=None):
        """Initialize authentication middleware."""
        super().__init__(app)
        self.settings = settings or get_settings()
        self.jwt_service = JWTService(self.settings)
        self.rate_limiter = UserRateLimiter(self.settings)
        
        # Paths that don't require authentication
        self.public_paths = {
            "/docs", "/redoc", "/openapi.json",
            "/health", "/",
            "/auth/login", "/auth/register", "/auth/refresh"
        }
    
    def _get_auth_service(self) -> AuthService:
        """Get authentication service instance."""
        return AuthService(self.settings, self.jwt_service)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None
    
    def _get_user_from_token(self, token: str, db: Session) -> Optional[User]:
        """Get user from JWT token."""
        try:
            auth_service = self._get_auth_service()
            return auth_service.get_current_user(db, token)
        except Exception as e:
            logger.debug(f"Token validation failed: {e}")
            return None
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require authentication)."""
        return any(path.startswith(public_path) for public_path in self.public_paths)
    
    def _get_endpoint_type(self, path: str, method: str) -> str:
        """Determine endpoint type for rate limiting."""
        if "/chat" in path:
            return "chat"
        elif "/models" in path or "/toolkits" in path:
            return "model_requests"
        elif "/auth" in path or "key" in path.lower():
            return "key_operations"
        else:
            return "general"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through authentication middleware."""
        start_time = time.time()
        
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        db = SessionLocal()
        try:
            # Extract token
            token = self._extract_token(request)
            user = None
            
            if token:
                user = self._get_user_from_token(token, db)
                
                if user:
                    # Check if user is active and not locked
                    if not user.is_active:
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "Inactive user"}
                        )
                    
                    if user.is_locked:
                        return JSONResponse(
                            status_code=status.HTTP_423_LOCKED,
                            content={"detail": "Account is locked"}
                        )
                    
                    # Apply rate limiting for authenticated users
                    endpoint_type = self._get_endpoint_type(request.url.path, request.method)
                    try:
                        self.rate_limiter.enforce_rate_limit(user.id, endpoint_type)
                    except HTTPException as e:
                        return JSONResponse(
                            status_code=e.status_code,
                            content={"detail": e.detail},
                            headers=e.headers
                        )
                    
                    # Add user to request state
                    request.state.user = user
                    request.state.user_id = user.id
                else:
                    # Invalid token
                    if not self._is_optional_auth_path(request.url.path):
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"detail": "Invalid authentication credentials"},
                            headers={"WWW-Authenticate": "Bearer"}
                        )
            else:
                # No token provided
                if not self._is_optional_auth_path(request.url.path):
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Authentication required"},
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            
            # Process request
            response = await call_next(request)
            
            # Add processing time header
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            # Add rate limit headers for authenticated users
            if user:
                stats = self.rate_limiter.get_user_stats(user.id)
                endpoint_type = self._get_endpoint_type(request.url.path, request.method)
                if endpoint_type in stats:
                    endpoint_stats = stats[endpoint_type]
                    response.headers["X-RateLimit-Limit"] = str(endpoint_stats["rate_limit"])
                    response.headers["X-RateLimit-Remaining"] = str(endpoint_stats["remaining"])
                    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
            
            return response
            
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
        finally:
            db.close()
    
    def _is_optional_auth_path(self, path: str) -> bool:
        """Check if path allows optional authentication."""
        # Some endpoints might work with or without authentication
        optional_auth_paths = [
            "/models",  # Public model list
            "/toolkits",  # Public toolkit list
        ]
        return any(path.startswith(optional_path) for optional_path in optional_auth_paths)