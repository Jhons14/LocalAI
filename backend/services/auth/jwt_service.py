"""
JWT token management service for authentication.
"""

from jose import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from config.settings import AppSettings


class JWTService:
    """Service for JWT token creation and validation."""
    
    def __init__(self, settings: AppSettings):
        """Initialize JWT service with app settings."""
        self.settings = settings
        self.secret_key = settings.security.secret_key
        self.algorithm = settings.security.algorithm
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes
    
    def create_access_token(self, user_id: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token for a user.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token as string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,  # Subject (user ID)
            "email": email,
            "exp": expire,   # Expiration time
            "iat": datetime.now(timezone.utc),  # Issued at
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str, email: str) -> str:
        """
        Create a JWT refresh token for a user.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            
        Returns:
            Encoded JWT refresh token as string
        """
        # Refresh tokens last 7 days
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        
        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                return None
                
            # Check if token is expired (jwt.decode already handles this, but explicit check)
            exp_timestamp = payload.get("exp")
            if exp_timestamp and datetime.fromtimestamp(exp_timestamp, timezone.utc) < datetime.now(timezone.utc):
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.JWTError:
            # Token is invalid
            return None
        except Exception:
            # Any other error
            return None
    
    def get_user_from_token(self, token: str) -> Optional[Dict[str, str]]:
        """
        Extract user information from a valid access token.
        
        Args:
            token: JWT access token
            
        Returns:
            Dictionary with user_id and email if valid, None if invalid
        """
        payload = self.verify_token(token, "access")
        if payload:
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email")
            }
        return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Create a new access token using a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token if refresh token is valid, None otherwise
        """
        payload = self.verify_token(refresh_token, "refresh")
        if payload:
            user_id = payload.get("sub")
            email = payload.get("email")
            if user_id and email:
                return self.create_access_token(user_id, email)
        return None
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired without validating signature.
        
        Args:
            token: JWT token to check
            
        Returns:
            True if expired, False if still valid or if token is malformed
        """
        try:
            # Decode without verification to check expiration
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp, timezone.utc) < datetime.now(timezone.utc)
            return True  # No expiration timestamp means invalid
        except Exception:
            return True  # Malformed token is considered expired