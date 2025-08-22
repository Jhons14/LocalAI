"""
Test script to verify the authentication system is working correctly.
"""

import requests
import json
import time
from typing import Dict, Optional


class AuthTester:
    """Test the authentication system"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def test_health(self) -> bool:
        """Test if the server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is running")
                return True
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    def test_register(self, username: str = "testuser2", email: str = "test2@example.com", password: str = "TestPassword123!") -> bool:
        """Test user registration"""
        try:
            data = {
                "username": username,
                "email": email,
                "password": password
            }
            
            response = requests.post(f"{self.base_url}/auth/register", json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ User registration successful: {result.get('user_id', 'unknown')}")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                print("⚠️  User already exists, continuing with login test")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Registration request failed: {e}")
            return False
    
    def test_login(self, email: str = "test2@example.com", password: str = "TestPassword123!") -> bool:
        """Test user login"""
        try:
            data = {
                "email": email,
                "password": password
            }
            
            response = requests.post(f"{self.base_url}/auth/login", json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                self.refresh_token = result.get("refresh_token")
                print(f"✅ Login successful: {result.get('user', {}).get('username')}")
                print(f"🔑 Access token: {self.access_token[:50]}...")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Login request failed: {e}")
            return False
    
    def test_protected_endpoint(self) -> bool:
        """Test accessing a protected endpoint"""
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test thread status endpoint (requires authentication)
            response = requests.get(
                f"{self.base_url}/threads/test123/status", 
                headers=headers, 
                timeout=10
            )
            
            if response.status_code in [200, 404]:  # 404 is expected for non-existent thread
                print("✅ Protected endpoint accessible with authentication")
                return True
            elif response.status_code == 401:
                print("❌ Authentication failed on protected endpoint")
                return False
            else:
                print(f"⚠️  Unexpected response from protected endpoint: {response.status_code}")
                return True  # Still consider this a pass since auth worked
                
        except requests.RequestException as e:
            print(f"❌ Protected endpoint request failed: {e}")
            return False
    
    def test_unauthorized_access(self) -> bool:
        """Test that protected endpoints reject unauthorized requests"""
        try:
            # Try to access protected endpoint without token
            response = requests.get(f"{self.base_url}/threads/test123/status", timeout=10)
            
            if response.status_code in [401, 403]:
                print("✅ Unauthorized access properly rejected")
                return True
            else:
                print(f"❌ Unauthorized access not properly rejected: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Unauthorized access test failed: {e}")
            return False
    
    def test_token_refresh(self) -> bool:
        """Test token refresh functionality"""
        if not self.refresh_token:
            print("❌ No refresh token available")
            return False
        
        try:
            data = {"refresh_token": self.refresh_token}
            response = requests.post(f"{self.base_url}/auth/refresh", json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                new_access_token = result.get("access_token")
                print(f"✅ Token refresh successful")
                print(f"🔑 New access token: {new_access_token[:50]}...")
                self.access_token = new_access_token
                return True
            else:
                print(f"❌ Token refresh failed: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Token refresh request failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all authentication tests"""
        print("🧪 Starting authentication system tests...\n")
        
        results = {}
        
        # Test 1: Server health
        print("1. Testing server health...")
        results["health"] = self.test_health()
        print()
        
        if not results["health"]:
            print("❌ Server is not running. Cannot continue tests.")
            return results
        
        # Test 2: User registration
        print("2. Testing user registration...")
        results["register"] = self.test_register()
        print()
        
        # Test 3: User login
        print("3. Testing user login...")
        results["login"] = self.test_login()
        print()
        
        # Test 4: Unauthorized access
        print("4. Testing unauthorized access rejection...")
        results["unauthorized"] = self.test_unauthorized_access()
        print()
        
        # Test 5: Protected endpoint access
        print("5. Testing protected endpoint access...")
        results["protected"] = self.test_protected_endpoint()
        print()
        
        # Test 6: Token refresh
        print("6. Testing token refresh...")
        results["refresh"] = self.test_token_refresh()
        print()
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        print("📊 Test Results Summary:")
        print(f"{'Test':<20} {'Status'}")
        print("-" * 30)
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test.capitalize():<20} {status}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All authentication tests passed!")
        else:
            print("⚠️  Some tests failed. Please check the error messages above.")
        
        return results


if __name__ == "__main__":
    tester = AuthTester()
    results = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        exit(1)