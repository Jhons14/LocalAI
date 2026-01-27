"""
Test script for password reset API endpoints.
This script tests the HTTP API endpoints for password reset functionality.
"""

import sys
import os
import requests
import json
import time

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_password_reset_endpoints():
    """Test password reset API endpoints."""
    base_url = "http://localhost:8003/auth"
    
    print("🚀 Testing Password Reset API Endpoints")
    print(f"Base URL: {base_url}")
    
    # Test data
    test_user = {
        "email": "apitest@example.com",
        "username": "apitest",
        "password": "TestPassword123!"
    }
    
    new_password = "NewPassword123!"
    
    try:
        # 1. Register a test user
        print("\n1. Registering test user...")
        response = requests.post(f"{base_url}/register", json=test_user)
        
        if response.status_code != 200:
            print(f"❌ User registration failed: {response.status_code} - {response.text}")
            return False
        
        user_data = response.json()
        print(f"✅ User registered: {user_data['email']}")
        
        # 2. Test forgot password endpoint
        print("\n2. Testing forgot password endpoint...")
        forgot_response = requests.post(
            f"{base_url}/forgot-password",
            json={"email": test_user["email"]}
        )
        
        if forgot_response.status_code != 200:
            print(f"❌ Forgot password request failed: {forgot_response.status_code} - {forgot_response.text}")
            return False
        
        forgot_data = forgot_response.json()
        print(f"✅ Forgot password response: {forgot_data['message']}")
        
        # 3. Test forgot password with non-existent email
        print("\n3. Testing forgot password with non-existent email...")
        forgot_invalid_response = requests.post(
            f"{base_url}/forgot-password",
            json={"email": "nonexistent@example.com"}
        )
        
        if forgot_invalid_response.status_code != 200:
            print(f"❌ Forgot password with invalid email failed: {forgot_invalid_response.status_code}")
            return False
        
        print("✅ Non-existent email handled correctly")
        
        # 4. Get reset token from database (for testing purposes)
        print("\n4. Getting reset token from database...")
        
        from database.base import get_db
        from database.models import User, PasswordResetToken
        
        with next(get_db()) as db:
            user = db.query(User).filter(User.email == test_user["email"]).first()
            if not user:
                print("❌ Test user not found in database")
                return False
            
            reset_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user.id
            ).order_by(PasswordResetToken.created_at.desc()).first()
            
            if not reset_token:
                print("❌ Reset token not found in database")
                return False
            
            token = reset_token.token
            print(f"✅ Found reset token: {token[:16]}...")
        
        # 5. Test verify reset token endpoint
        print("\n5. Testing verify reset token endpoint...")
        verify_response = requests.get(f"{base_url}/verify-reset-token/{token}")
        
        if verify_response.status_code != 200:
            print(f"❌ Token verification failed: {verify_response.status_code} - {verify_response.text}")
            return False
        
        verify_data = verify_response.json()
        print(f"✅ Token verification: {verify_data['message']}")
        
        # 6. Test verify invalid token
        print("\n6. Testing verify invalid token...")
        invalid_verify_response = requests.get(f"{base_url}/verify-reset-token/invalid-token")
        
        if invalid_verify_response.status_code == 200:
            print("❌ Invalid token should have failed verification")
            return False
        
        print("✅ Invalid token correctly rejected")
        
        # 7. Test reset password endpoint
        print("\n7. Testing reset password endpoint...")
        reset_response = requests.post(
            f"{base_url}/reset-password",
            json={
                "token": token,
                "new_password": new_password
            }
        )
        
        if reset_response.status_code != 200:
            print(f"❌ Password reset failed: {reset_response.status_code} - {reset_response.text}")
            return False
        
        reset_data = reset_response.json()
        print(f"✅ Password reset: {reset_data['message']}")
        
        # 8. Test login with new password
        print("\n8. Testing login with new password...")
        login_response = requests.post(
            f"{base_url}/login",
            json={
                "email": test_user["email"],
                "password": new_password
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login with new password failed: {login_response.status_code} - {login_response.text}")
            return False
        
        print("✅ Login with new password successful")
        
        # 9. Test login with old password (should fail)
        print("\n9. Testing login with old password...")
        old_login_response = requests.post(
            f"{base_url}/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        
        if old_login_response.status_code == 200:
            print("❌ Login with old password should have failed")
            return False
        
        print("✅ Login with old password correctly rejected")
        
        # 10. Test reusing token (should fail)
        print("\n10. Testing token reuse...")
        reuse_response = requests.post(
            f"{base_url}/reset-password",
            json={
                "token": token,
                "new_password": "AnotherPassword123!"
            }
        )
        
        if reuse_response.status_code == 200:
            print("❌ Token reuse should have failed")
            return False
        
        print("✅ Token reuse correctly prevented")
        
        print("\n🎉 All API endpoint tests passed!")
        return True
        
    except requests.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on localhost:8003")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

def main():
    """Main function to run API endpoint tests."""
    print("=" * 60)
    print("🔗 PASSWORD RESET API ENDPOINT TESTS")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8003/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server health check failed")
            print("Please start the server with: python3 main.py")
            return False
        print("✅ Server is running")
    except requests.ConnectionError:
        print("❌ Cannot connect to server on localhost:8003")
        print("Please start the server with: python3 main.py")
        return False
    
    success = test_password_reset_endpoints()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL API ENDPOINT TESTS PASSED")
    else:
        print("❌ SOME API ENDPOINT TESTS FAILED")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)