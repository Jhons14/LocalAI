"""
Password hashing and validation service using bcrypt.
"""

import bcrypt
from typing import str


class PasswordService:
    """Service for secure password hashing and validation."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with salt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password as string
        """
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds for good security/performance balance
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Previously hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except (ValueError, TypeError):
            # Handle malformed hashes gracefully
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """
        Validate password meets security requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            errors.append("Password must be less than 128 characters")
            
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
            
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
            
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
            
        # Check for special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors