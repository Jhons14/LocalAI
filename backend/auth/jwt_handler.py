"""
JWT token handling for authentication and authorization.
Provides secure token generation, validation, and user authentication.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from config.settings import AppSettings

logger = logging.getLogger(__name__)


class JWTHandler:
    """Handles JWT token operations for user authentication."""
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.secret_key = settings.security.secret_key
        self.algorithm = settings.security.algorithm
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a new JWT access token.
        
        Args:
            data: Data to encode in the token (typically user_id, email, etc.)
            expires_delta: Custom expiration time (optional)
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        # Set expiration time
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Access token created for user: {data.get('sub', 'unknown')}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise ValueError("Failed to create access token")
    
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a new JWT refresh token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Custom expiration time (default: 7 days)
            
        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        
        # Set expiration time (longer for refresh tokens)
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Refresh token created for user: {data.get('sub', 'unknown')}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise ValueError("Failed to create refresh token")
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(f"Invalid token type. Expected: {token_type}, Got: {payload.get('type')}")
                return None
            
            # Check expiration
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                if datetime.now(timezone.utc) > exp_datetime:
                    logger.warning("Token has expired")
                    return None
            
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Extract user ID from a valid token.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID or None if invalid
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired without full verification.
        
        Args:
            token: JWT token string
            
        Returns:
            True if expired, False otherwise
        """
        try:
            # Decode without verification to check expiration
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get("exp")
            
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                return datetime.now(timezone.utc) > exp_datetime
                
            return True  # No expiration means invalid
            
        except Exception:
            return True  # Any error means treat as expired
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (for logout functionality).
        Note: In a production system, you'd typically store revoked tokens
        in a database or cache like Redis.
        
        Args:
            token: JWT token to revoke
            
        Returns:
            True if successfully revoked
        """
        # For now, we'll just validate the token exists
        payload = self.verify_token(token)
        if payload:
            logger.info(f"Token revoked for user: {payload.get('sub', 'unknown')}")
            # TODO: Store revoked token in database/cache
            return True
        return False