"""
Main authentication service orchestrating user authentication operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from database.models import User
from .password_service import PasswordService
from .jwt_service import JWTService
from config.settings import AppSettings


class AuthService:
    """Main authentication service coordinating user operations."""
    
    def __init__(self, settings: AppSettings, jwt_service: JWTService):
        """Initialize authentication service."""
        self.settings = settings
        self.jwt_service = jwt_service
        self.password_service = PasswordService()
    
    def register_user(self, db: Session, email: str, username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Register a new user account.
        
        Args:
            db: Database session
            email: User's email address
            username: User's username
            password: Plain text password
            
        Returns:
            Tuple of (success, message, user_data_with_tokens)
        """
        # Validate password strength
        is_valid, password_errors = self.password_service.validate_password_strength(password)
        if not is_valid:
            return False, "; ".join(password_errors), None
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                return False, "Email already registered", None
            else:
                return False, "Username already taken", None
        
        try:
            # Hash password
            hashed_password = self.password_service.hash_password(password)
            
            # Create new user
            new_user = User(
                email=email,
                username=username,
                hashed_password=hashed_password,
                is_active=True,
                is_admin=False
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Generate tokens
            access_token = self.jwt_service.create_access_token(new_user.id, new_user.email)
            refresh_token = self.jwt_service.create_refresh_token(new_user.id, new_user.email)
            
            user_data = {
                "user_id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "is_admin": new_user.is_admin,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
            return True, "User registered successfully", user_data
            
        except Exception as e:
            db.rollback()
            return False, f"Registration failed: {str(e)}", None
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate a user with email and password.
        
        Args:
            db: Database session
            email: User's email address
            password: Plain text password
            
        Returns:
            Tuple of (success, message, user_data_with_tokens)
        """
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False, "Invalid email or password", None
        
        # Check if user is locked
        if user.is_locked:
            return False, f"Account locked until {user.locked_until.strftime('%Y-%m-%d %H:%M:%S UTC')}", None
        
        # Check if user is active
        if not user.is_active:
            return False, "Account deactivated", None
        
        # Verify password
        if not self.password_service.verify_password(password, user.hashed_password):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= self.settings.security.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=self.settings.security.lockout_duration_minutes
                )
            
            db.commit()
            return False, "Invalid email or password", None
        
        try:
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            
            db.commit()
            
            # Generate tokens
            access_token = self.jwt_service.create_access_token(user.id, user.email)
            refresh_token = self.jwt_service.create_refresh_token(user.id, user.email)
            
            user_data = {
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
            return True, "Login successful", user_data
            
        except Exception as e:
            db.rollback()
            return False, f"Login failed: {str(e)}", None
    
    def refresh_token(self, refresh_token: str) -> Tuple[bool, str, Optional[str]]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Tuple of (success, message, new_access_token)
        """
        new_access_token = self.jwt_service.refresh_access_token(refresh_token)
        if new_access_token:
            return True, "Token refreshed successfully", new_access_token
        else:
            return False, "Invalid or expired refresh token", None
    
    def get_current_user(self, db: Session, access_token: str) -> Optional[User]:
        """
        Get current user from access token.
        
        Args:
            db: Database session
            access_token: JWT access token
            
        Returns:
            User object if token is valid, None otherwise
        """
        user_info = self.jwt_service.get_user_from_token(access_token)
        if not user_info:
            return None
        
        user = db.query(User).filter(User.id == user_info["user_id"]).first()
        if user and user.is_active and not user.is_locked:
            return user
        
        return None
    
    def change_password(self, db: Session, user_id: str, current_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user's password.
        
        Args:
            db: Database session
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Tuple of (success, message)
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not self.password_service.verify_password(current_password, user.hashed_password):
            return False, "Current password is incorrect"
        
        # Validate new password
        is_valid, password_errors = self.password_service.validate_password_strength(new_password)
        if not is_valid:
            return False, "; ".join(password_errors)
        
        try:
            # Hash and update password
            user.hashed_password = self.password_service.hash_password(new_password)
            db.commit()
            
            return True, "Password changed successfully"
            
        except Exception as e:
            db.rollback()
            return False, f"Password change failed: {str(e)}"