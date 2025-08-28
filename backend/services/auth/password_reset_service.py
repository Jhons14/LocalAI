"""
Password reset service for handling forgotten password functionality.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database.models import User, PasswordResetToken
from .password_service import PasswordService
from config.settings import AppSettings
from services.email_service import EmailService


class PasswordResetService:
    """Service for handling password reset operations."""
    
    def __init__(self, settings: AppSettings):
        """Initialize password reset service."""
        self.settings = settings
        self.password_service = PasswordService()
        self.email_service = EmailService(settings.email_config)
    
    def generate_reset_token(self, db: Session, email: str, client_ip: str = None, user_agent: str = None) -> Tuple[bool, str]:
        """
        Generate a password reset token for the given email.
        
        Args:
            db: Database session
            email: User's email address
            client_ip: Client IP address for security logging
            user_agent: Client user agent for security logging
            
        Returns:
            Tuple of (success, message)
        """
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        # Always return success to prevent email enumeration
        # but only actually create token if user exists
        if user and user.is_active:
            try:
                # Clean up old expired tokens for this user
                self._cleanup_expired_tokens(db, user.id)
                
                # Check rate limiting - max 5 reset requests per hour per user
                recent_tokens = db.query(PasswordResetToken).filter(
                    and_(
                        PasswordResetToken.user_id == user.id,
                        PasswordResetToken.created_at > datetime.utcnow() - timedelta(hours=1)
                    )
                ).count()
                if recent_tokens >= 5:
                    return True, "If your email is in our system, you will receive reset instructions shortly."
                
                # Generate secure token
                token = secrets.token_urlsafe(32)  # 43 characters, URL-safe
                
                # Create reset token record
                reset_token = PasswordResetToken(
                    user_id=user.id,
                    token=token,
                    expires_at=datetime.utcnow() + timedelta(hours=self.settings.security.reset_token_expire_hours or 6),
                    requested_ip=client_ip,
                    requested_user_agent=user_agent
                )
                
                db.add(reset_token)
                db.commit()
                
                # Send password reset email
                email_sent = self.email_service.send_password_reset_email(
                    to_email=email,
                    reset_token=token,
                    user_name=user.username
                )
                
                if not email_sent:
                    print(f"Warning: Failed to send password reset email to {email}")
                    # Still return success to prevent email enumeration
                
            except Exception as e:
                db.rollback()
                print(f"Error generating reset token: {str(e)}")
        
        return True, "If your email is in our system, you will receive reset instructions shortly."
    
    def verify_reset_token(self, db: Session, token: str) -> Tuple[bool, str, Optional[str]]:
        """
        Verify a password reset token.
        
        Args:
            db: Database session
            token: Reset token to verify
            
        Returns:
            Tuple of (is_valid, message, user_id)
        """
        try:
            reset_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            
            if not reset_token:
                return False, "Invalid or expired reset token", None
            
            if reset_token.is_used:
                return False, "Reset token has already been used", None
            
            if reset_token.is_expired:
                return False, "Reset token has expired", None
            
            # Check if user is still active
            user = db.query(User).filter(User.id == reset_token.user_id).first()
            if not user or not user.is_active:
                return False, "Invalid or expired reset token", None
            
            return True, "Token is valid", reset_token.user_id
            
        except Exception as e:
            print(f"Error verifying reset token: {str(e)}")
            return False, "Invalid or expired reset token", None
    
    def reset_password(self, db: Session, token: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset password using a valid reset token.
        
        Args:
            db: Database session
            token: Valid reset token
            new_password: New password to set
            
        Returns:
            Tuple of (success, message)
        """
        # Verify token first
        is_valid, message, user_id = self.verify_reset_token(db, token)
        if not is_valid:
            return False, message
        
        # Validate new password strength
        is_strong, password_errors = self.password_service.validate_password_strength(new_password)
        if not is_strong:
            return False, "; ".join(password_errors)
        
        try:
            # Get user and reset token
            user = db.query(User).filter(User.id == user_id).first()
            reset_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            
            if not user or not reset_token:
                return False, "Invalid reset token"
            
            # Update password
            user.hashed_password = self.password_service.hash_password(new_password)
            
            # Reset failed login attempts and unlock account
            user.failed_login_attempts = 0
            user.locked_until = None
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.used_at = datetime.utcnow()
            
            db.commit()
            
            # Clean up all other reset tokens for this user
            self._cleanup_user_tokens(db, user_id)
            
            return True, "Password has been reset successfully"
            
        except Exception as e:
            db.rollback()
            print(f"Error resetting password: {str(e)}")
            return False, "Password reset failed. Please try again."
    
    def _cleanup_expired_tokens(self, db: Session, user_id: str = None):
        """Clean up expired reset tokens."""
        try:
            query = db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < datetime.utcnow()
            )
            
            if user_id:
                query = query.filter(PasswordResetToken.user_id == user_id)
            
            expired_tokens = query.all()
            for token in expired_tokens:
                db.delete(token)
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error cleaning up expired tokens: {str(e)}")
    
    def _cleanup_user_tokens(self, db: Session, user_id: str):
        """Clean up all unused reset tokens for a user."""
        try:
            unused_tokens = db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.user_id == user_id,
                    PasswordResetToken.is_used == False
                )
            ).all()
            
            for token in unused_tokens:
                db.delete(token)
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error cleaning up user tokens: {str(e)}")
    
    def cleanup_expired_tokens_globally(self, db: Session) -> int:
        """
        Clean up all expired reset tokens globally.
        This should be called periodically (e.g., daily cron job).
        
        Returns:
            Number of tokens cleaned up
        """
        try:
            expired_tokens = db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < datetime.utcnow()
            ).all()
            
            count = len(expired_tokens)
            
            for token in expired_tokens:
                db.delete(token)
            
            db.commit()
            
            return count
        except Exception as e:
            db.rollback()
            print(f"Error in global token cleanup: {str(e)}")
            return 0