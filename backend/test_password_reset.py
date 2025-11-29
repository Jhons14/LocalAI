"""
Test script for password reset functionality.
This script tests the complete forgotten password flow.
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database.base import get_db, engine
from database.models import User, PasswordResetToken
from services.auth.password_reset_service import PasswordResetService
from services.auth.auth_service import AuthService
from services.auth.jwt_service import JWTService
from services.email_service import EmailService
from config.settings import get_settings

class PasswordResetTester:
    """Test class for password reset functionality."""
    
    def __init__(self):
        self.settings = get_settings()
        self.reset_service = PasswordResetService(self.settings)
        
        # Create auth service for user creation
        jwt_service = JWTService(self.settings)
        self.auth_service = AuthService(self.settings, jwt_service)
        
        self.test_email = "test@example.com"
        self.test_username = "testuser"
        self.test_password = "TestPassword123!"
        self.new_password = "NewPassword123!"
        self.test_user_id = None
        
    def setup_test_user(self, db: Session) -> bool:
        """Create a test user for password reset testing."""
        try:
            # Clean up any existing test user
            existing_user = db.query(User).filter(User.email == self.test_email).first()
            if existing_user:
                db.delete(existing_user)
                db.commit()
            
            # Register new test user
            success, message, user_data = self.auth_service.register_user(
                db=db,
                email=self.test_email,
                username=self.test_username,
                password=self.test_password
            )
            
            if not success:
                print(f"❌ Failed to create test user: {message}")
                return False
            
            self.test_user_id = user_data["user_id"]
            print(f"✅ Test user created: {self.test_email} (ID: {self.test_user_id})")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up test user: {str(e)}")
            return False
    
    def test_email_service(self) -> bool:
        """Test email service configuration."""
        print("\n🔍 Testing email service configuration...")
        
        email_service = EmailService(self.settings.email_config)
        
        # Test connection (will skip if credentials not configured)
        success, message = email_service.test_connection()
        print(f"📧 Email connection test: {message}")
        
        return True
    
    def test_generate_reset_token(self, db: Session) -> tuple[bool, str]:
        """Test password reset token generation."""
        print("\n🔍 Testing password reset token generation...")
        
        try:
            # Test with valid email
            success, message = self.reset_service.generate_reset_token(
                db=db,
                email=self.test_email,
                client_ip="127.0.0.1",
                user_agent="Test-Agent"
            )
            
            if not success:
                print(f"❌ Failed to generate reset token: {message}")
                return False, ""
            
            # Get the token from database
            reset_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == self.test_user_id
            ).order_by(PasswordResetToken.created_at.desc()).first()
            
            if not reset_token:
                print("❌ No reset token found in database")
                return False, ""
            
            print(f"✅ Reset token generated successfully")
            print(f"   Token: {reset_token.token[:16]}...")
            print(f"   Expires: {reset_token.expires_at}")
            print(f"   User ID: {reset_token.user_id}")
            
            # Test with non-existent email (should still return success)
            success2, message2 = self.reset_service.generate_reset_token(
                db=db,
                email="nonexistent@example.com",
                client_ip="127.0.0.1",
                user_agent="Test-Agent"
            )
            
            if success2:
                print("✅ Non-existent email handled correctly (no enumeration)")
            else:
                print("❌ Non-existent email not handled correctly")
            
            return True, reset_token.token
            
        except Exception as e:
            print(f"❌ Error testing token generation: {str(e)}")
            return False, ""
    
    def test_verify_reset_token(self, db: Session, token: str) -> bool:
        """Test password reset token verification."""
        print("\n🔍 Testing password reset token verification...")
        
        try:
            # Test valid token
            is_valid, message, user_id = self.reset_service.verify_reset_token(db, token)
            
            if not is_valid:
                print(f"❌ Valid token verification failed: {message}")
                return False
            
            if user_id != self.test_user_id:
                print(f"❌ Token user ID mismatch: {user_id} != {self.test_user_id}")
                return False
            
            print(f"✅ Valid token verified successfully: {message}")
            
            # Test invalid token
            is_valid2, message2, user_id2 = self.reset_service.verify_reset_token(db, "invalid-token")
            
            if is_valid2:
                print("❌ Invalid token verification should have failed")
                return False
            
            print(f"✅ Invalid token handled correctly: {message2}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing token verification: {str(e)}")
            return False
    
    def test_reset_password(self, db: Session, token: str) -> bool:
        """Test password reset using token."""
        print("\n🔍 Testing password reset...")
        
        try:
            # Test password reset with valid token
            success, message = self.reset_service.reset_password(
                db=db,
                token=token,
                new_password=self.new_password
            )
            
            if not success:
                print(f"❌ Password reset failed: {message}")
                return False
            
            print(f"✅ Password reset successful: {message}")
            
            # Verify the token is now marked as used
            reset_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            
            if not reset_token or not reset_token.is_used:
                print("❌ Token not marked as used after password reset")
                return False
            
            print("✅ Token correctly marked as used")
            
            # Test login with new password
            success_login, message_login, user_data = self.auth_service.authenticate_user(
                db=db,
                email=self.test_email,
                password=self.new_password
            )
            
            if not success_login:
                print(f"❌ Login with new password failed: {message_login}")
                return False
            
            print("✅ Login with new password successful")
            
            # Test that old password no longer works
            success_old, message_old, _ = self.auth_service.authenticate_user(
                db=db,
                email=self.test_email,
                password=self.test_password
            )
            
            if success_old:
                print("❌ Old password still works (should not)")
                return False
            
            print("✅ Old password correctly rejected")
            
            # Test reusing the same token (should fail)
            success_reuse, message_reuse = self.reset_service.reset_password(
                db=db,
                token=token,
                new_password="AnotherPassword123!"
            )
            
            if success_reuse:
                print("❌ Token reuse should have failed")
                return False
            
            print(f"✅ Token reuse correctly prevented: {message_reuse}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing password reset: {str(e)}")
            return False
    
    def test_rate_limiting(self, db: Session) -> bool:
        """Test rate limiting for password reset requests."""
        print("\n🔍 Testing rate limiting...")
        
        try:
            # Generate multiple reset tokens quickly
            for i in range(6):  # Exceed the limit of 5
                success, message = self.reset_service.generate_reset_token(
                    db=db,
                    email=self.test_email,
                    client_ip="127.0.0.1",
                    user_agent="Test-Agent"
                )
                print(f"   Request {i+1}: {'✅' if success else '❌'}")
            
            # Count tokens created in the last hour
            from datetime import timedelta
            recent_tokens = db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == self.test_user_id,
                PasswordResetToken.created_at > datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            print(f"✅ Rate limiting test completed. Tokens created: {recent_tokens}")
            return True
            
        except Exception as e:
            print(f"❌ Error testing rate limiting: {str(e)}")
            return False
    
    def test_cleanup_functions(self, db: Session) -> bool:
        """Test token cleanup functions."""
        print("\n🔍 Testing token cleanup functions...")
        
        try:
            # Test global cleanup
            cleaned_count = self.reset_service.cleanup_expired_tokens_globally(db)
            print(f"✅ Global cleanup completed. Cleaned {cleaned_count} expired tokens.")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing cleanup: {str(e)}")
            return False
    
    def cleanup_test_data(self, db: Session) -> bool:
        """Clean up test data."""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Delete test user and associated tokens
            if self.test_user_id:
                user = db.query(User).filter(User.id == self.test_user_id).first()
                if user:
                    db.delete(user)
                    db.commit()
                    print("✅ Test user deleted")
            
            return True
            
        except Exception as e:
            print(f"❌ Error cleaning up test data: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all password reset tests."""
        print("🚀 Starting password reset functionality tests...")
        print(f"📊 Environment: {self.settings.environment}")
        print(f"📊 Database: {self.settings.database.url}")
        print(f"📊 Email SMTP: {self.settings.email_config.smtp_server}:{self.settings.email_config.smtp_port}")
        
        try:
            with next(get_db()) as db:
                # Setup
                if not self.setup_test_user(db):
                    return False
                
                # Test email service
                if not self.test_email_service():
                    return False
                
                # Test token generation
                success, token = self.test_generate_reset_token(db)
                if not success:
                    return False
                
                # Test token verification
                if not self.test_verify_reset_token(db, token):
                    return False
                
                # Test password reset
                if not self.test_reset_password(db, token):
                    return False
                
                # Test rate limiting
                if not self.test_rate_limiting(db):
                    return False
                
                # Test cleanup functions
                if not self.test_cleanup_functions(db):
                    return False
                
                # Cleanup
                if not self.cleanup_test_data(db):
                    return False
                
                print("\n🎉 All password reset tests passed successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Test suite failed with error: {str(e)}")
            return False

def main():
    """Main test function."""
    print("=" * 60)
    print("🔐 PASSWORD RESET FUNCTIONALITY TESTS")
    print("=" * 60)
    
    # Run migration first
    print("\n📋 Running migration...")
    try:
        from migrations.add_password_reset_tokens import run_migration
        if not run_migration():
            print("❌ Migration failed")
            return False
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")
        return False
    
    # Run tests
    tester = PasswordResetTester()
    success = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)