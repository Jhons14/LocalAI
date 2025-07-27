"""
Password handling utilities for secure authentication.
Provides password hashing, verification, and strength validation.
"""

import re
import logging
from typing import Optional, List, Dict
from passlib.context import CryptContext
from passlib.hash import bcrypt

logger = logging.getLogger(__name__)


class PasswordHandler:
    """Handles password hashing, verification, and validation."""
    
    def __init__(self):
        # Configure password hashing context
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12  # Secure but not too slow
        )
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
            
        Raises:
            ValueError: If password is empty or None
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        try:
            hashed = self.pwd_context.hash(password)
            logger.debug("Password hashed successfully")
            return hashed
            
        except Exception as e:
            logger.error(f"Failed to hash password: {e}")
            raise ValueError("Failed to hash password")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hash to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        if not plain_password or not hashed_password:
            return False
        
        try:
            is_valid = self.pwd_context.verify(plain_password, hashed_password)
            logger.debug(f"Password verification result: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def needs_update(self, hashed_password: str) -> bool:
        """
        Check if a password hash needs to be updated.
        
        Args:
            hashed_password: Stored password hash
            
        Returns:
            True if hash should be updated, False otherwise
        """
        try:
            return self.pwd_context.needs_update(hashed_password)
        except Exception:
            return True  # If we can't determine, assume it needs update
    
    def validate_password_strength(self, password: str) -> Dict[str, any]:
        """
        Validate password strength and return detailed feedback.
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results and feedback
        """
        validation_result = {
            "is_valid": False,
            "score": 0,
            "feedback": [],
            "requirements_met": {}
        }
        
        if not password:
            validation_result["feedback"].append("Password is required")
            return validation_result
        
        # Define password requirements
        requirements = {
            "min_length": len(password) >= 8,
            "max_length": len(password) <= 128,
            "has_uppercase": bool(re.search(r'[A-Z]', password)),
            "has_lowercase": bool(re.search(r'[a-z]', password)),
            "has_digit": bool(re.search(r'\d', password)),
            "has_special": bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\?]', password)),
            "no_common_patterns": not self._has_common_patterns(password),
            "no_repeated_chars": not self._has_excessive_repeated_chars(password)
        }
        
        validation_result["requirements_met"] = requirements
        
        # Calculate score based on requirements met
        score = sum(requirements.values())
        validation_result["score"] = (score / len(requirements)) * 100
        
        # Generate feedback
        feedback = []
        
        if not requirements["min_length"]:
            feedback.append("Password must be at least 8 characters long")
        if not requirements["max_length"]:
            feedback.append("Password must be no more than 128 characters long")
        if not requirements["has_uppercase"]:
            feedback.append("Password must contain at least one uppercase letter")
        if not requirements["has_lowercase"]:
            feedback.append("Password must contain at least one lowercase letter")
        if not requirements["has_digit"]:
            feedback.append("Password must contain at least one digit")
        if not requirements["has_special"]:
            feedback.append("Password must contain at least one special character")
        if not requirements["no_common_patterns"]:
            feedback.append("Password contains common patterns or sequences")
        if not requirements["no_repeated_chars"]:
            feedback.append("Password has too many repeated characters")
        
        # Determine if password is valid (require minimum security level)
        required_checks = ["min_length", "has_uppercase", "has_lowercase", "has_digit"]
        validation_result["is_valid"] = all(requirements[check] for check in required_checks)
        
        if validation_result["is_valid"] and len(feedback) == 0:
            feedback.append("Password meets security requirements")
        
        validation_result["feedback"] = feedback
        
        return validation_result
    
    def _has_common_patterns(self, password: str) -> bool:
        """Check for common password patterns."""
        password_lower = password.lower()
        
        # Common patterns to avoid
        common_patterns = [
            "password", "123456", "qwerty", "abc", "admin", "user", "login",
            "welcome", "hello", "test", "guest", "demo", "temp", "pass"
        ]
        
        # Check for common words
        for pattern in common_patterns:
            if pattern in password_lower:
                return True
        
        # Check for keyboard patterns
        keyboard_patterns = [
            "qwertyuiop", "asdfghjkl", "zxcvbnm",
            "1234567890", "0987654321"
        ]
        
        for pattern in keyboard_patterns:
            if pattern in password_lower or pattern[::-1] in password_lower:
                return True
        
        # Check for date patterns (YYYY, MMDD, etc.)
        if re.search(r'19\d{2}|20\d{2}', password):
            return True
        
        return False
    
    def _has_excessive_repeated_chars(self, password: str, max_repeats: int = 3) -> bool:
        """Check for excessive character repetition."""
        for i in range(len(password) - max_repeats):
            if len(set(password[i:i + max_repeats + 1])) == 1:
                return True
        return False
    
    def generate_password_suggestions(self) -> List[str]:
        """
        Generate secure password suggestions.
        
        Returns:
            List of secure password suggestions
        """
        # This is a simple implementation - in production, you might use
        # a more sophisticated password generator
        import secrets
        import string
        
        suggestions = []
        
        for _ in range(3):
            # Generate a secure random password
            length = secrets.randbelow(8) + 12  # 12-19 characters
            
            # Ensure we have all required character types
            chars = (
                secrets.choice(string.ascii_uppercase) +
                secrets.choice(string.ascii_lowercase) +
                secrets.choice(string.digits) +
                secrets.choice("!@#$%^&*")
            )
            
            # Fill the rest with random characters
            all_chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
            for _ in range(length - 4):
                chars += secrets.choice(all_chars)
            
            # Shuffle the characters
            chars_list = list(chars)
            secrets.SystemRandom().shuffle(chars_list)
            password = ''.join(chars_list)
            
            suggestions.append(password)
        
        return suggestions