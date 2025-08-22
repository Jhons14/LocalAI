"""
API key encryption service for secure storage.
"""

import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import str, Optional
from config.settings import AppSettings


class EncryptionService:
    """Service for encrypting and decrypting API keys."""
    
    def __init__(self, settings: AppSettings):
        """Initialize encryption service with app settings."""
        self.settings = settings
        self.master_key = settings.security.api_key_encryption_key or settings.security.secret_key
    
    def _derive_key(self, user_id: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """
        Derive encryption key from master key and user ID.
        
        Args:
            user_id: User's unique identifier
            salt: Optional salt for key derivation
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = hashlib.sha256(user_id.encode()).digest()[:16]  # 16 bytes salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes = 256 bits
            salt=salt,
            iterations=100000,  # High iteration count for security
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return key, salt
    
    def encrypt_api_key(self, api_key: str, user_id: str) -> str:
        """
        Encrypt an API key for storage.
        
        Args:
            api_key: Plain text API key to encrypt
            user_id: User ID for key derivation
            
        Returns:
            Base64 encoded encrypted API key
        """
        key, salt = self._derive_key(user_id)
        fernet = Fernet(key)
        
        # Encrypt the API key
        encrypted_key = fernet.encrypt(api_key.encode())
        
        # Combine salt and encrypted key for storage
        combined = salt + encrypted_key
        
        return base64.urlsafe_b64encode(combined).decode()
    
    def decrypt_api_key(self, encrypted_api_key: str, user_id: str) -> Optional[str]:
        """
        Decrypt an API key from storage.
        
        Args:
            encrypted_api_key: Base64 encoded encrypted API key
            user_id: User ID for key derivation
            
        Returns:
            Decrypted API key as string, None if decryption fails
        """
        try:
            # Decode the combined data
            combined = base64.urlsafe_b64decode(encrypted_api_key.encode())
            
            # Extract salt and encrypted key
            salt = combined[:16]  # First 16 bytes are salt
            encrypted_key = combined[16:]  # Rest is encrypted key
            
            # Derive the same key using the salt
            key, _ = self._derive_key(user_id, salt)
            fernet = Fernet(key)
            
            # Decrypt the API key
            decrypted_key = fernet.decrypt(encrypted_key)
            
            return decrypted_key.decode()
            
        except Exception:
            # Return None if decryption fails for any reason
            return None
    
    def rotate_encryption(self, old_encrypted_key: str, user_id: str, new_master_key: Optional[str] = None) -> Optional[str]:
        """
        Rotate encryption by re-encrypting with new master key.
        
        Args:
            old_encrypted_key: Previously encrypted API key
            user_id: User ID for key derivation
            new_master_key: Optional new master key (uses current if None)
            
        Returns:
            Re-encrypted API key, None if operation fails
        """
        # Decrypt with current master key
        plain_key = self.decrypt_api_key(old_encrypted_key, user_id)
        if plain_key is None:
            return None
        
        # Temporarily update master key if provided
        original_master_key = self.master_key
        if new_master_key:
            self.master_key = new_master_key
        
        try:
            # Re-encrypt with new master key
            new_encrypted_key = self.encrypt_api_key(plain_key, user_id)
            return new_encrypted_key
        finally:
            # Restore original master key
            self.master_key = original_master_key
    
    def validate_encryption_key(self) -> bool:
        """
        Validate that the encryption key is properly configured.
        
        Returns:
            True if encryption key is valid, False otherwise
        """
        if not self.master_key:
            return False
        
        if len(self.master_key) < 32:
            return False
        
        # Test encryption/decryption cycle
        try:
            test_key = "test-api-key-123"
            test_user = "test-user-id"
            
            encrypted = self.encrypt_api_key(test_key, test_user)
            decrypted = self.decrypt_api_key(encrypted, test_user)
            
            return decrypted == test_key
        except Exception:
            return False