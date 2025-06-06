"""
Encryption service for securing sensitive data in NumerusX.
Provides encryption/decryption for API keys and other sensitive configuration data.
"""

import os
import base64
import logging
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    _fernet = None
    _master_key = None
    
    @classmethod
    def _get_master_key(cls) -> str:
        """Get or generate master encryption key."""
        if cls._master_key is None:
            # Try to get from environment first
            cls._master_key = os.getenv('MASTER_ENCRYPTION_KEY')
            
            if not cls._master_key:
                # Generate a new key if none exists
                cls._master_key = cls._generate_key()
                logger.warning("No MASTER_ENCRYPTION_KEY found, generated new key. "
                              "Save this key securely: " + cls._master_key)
        
        return cls._master_key
    
    @classmethod
    def _generate_key(cls) -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode()
    
    @classmethod
    def _get_fernet(cls) -> Fernet:
        """Get Fernet cipher instance."""
        if cls._fernet is None:
            key = cls._get_master_key()
            
            # If key is a password/passphrase, derive a proper key
            if len(key) != 44:  # Fernet keys are 44 characters
                key_bytes = cls._derive_key_from_password(key)
            else:
                key_bytes = key.encode()
            
            cls._fernet = Fernet(key_bytes)
        
        return cls._fernet
    
    @classmethod
    def _derive_key_from_password(cls, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive a Fernet key from a password."""
        if salt is None:
            # Use a fixed salt for consistency (in production, consider storing salt)
            salt = b'numerusx_salt_2024'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @classmethod
    def encrypt_data(cls, data: Union[str, bytes]) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: String or bytes to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            fernet = cls._get_fernet()
            encrypted = fernet.encrypt(data)
            
            # Return as base64 string for easy storage
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")
    
    @classmethod
    def decrypt_data(cls, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Base64 encoded encrypted string
            
        Returns:
            Decrypted string
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            fernet = cls._get_fernet()
            decrypted = fernet.decrypt(encrypted_bytes)
            
            return decrypted.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")
    
    @classmethod
    def is_encrypted(cls, data: str) -> bool:
        """
        Check if data appears to be encrypted.
        
        Args:
            data: String to check
            
        Returns:
            True if data appears encrypted, False otherwise
        """
        try:
            # Try to decode as base64 - encrypted data should be base64 encoded
            decoded = base64.b64decode(data.encode('utf-8'))
            # Additional check: encrypted data should be at least a certain length
            return len(decoded) >= 16  # Fernet adds overhead
        except:
            return False
    
    @classmethod
    def encrypt_dict(cls, data_dict: dict, keys_to_encrypt: list = None) -> dict:
        """
        Encrypt specific keys in a dictionary.
        
        Args:
            data_dict: Dictionary to process
            keys_to_encrypt: List of keys to encrypt (if None, encrypts sensitive keys)
            
        Returns:
            Dictionary with encrypted values
        """
        if keys_to_encrypt is None:
            # Default sensitive keys
            keys_to_encrypt = [
                'api_key', 'secret', 'password', 'private_key', 'token',
                'jwt_secret', 'encryption_key', 'wallet_key', 'credentials'
            ]
        
        result = data_dict.copy()
        
        for key, value in result.items():
            # Check if key contains sensitive terms
            should_encrypt = any(sensitive in key.lower() for sensitive in keys_to_encrypt)
            
            if should_encrypt and value and isinstance(value, str):
                # Only encrypt if not already encrypted
                if not cls.is_encrypted(value):
                    try:
                        result[key] = cls.encrypt_data(value)
                        logger.debug(f"Encrypted field: {key}")
                    except Exception as e:
                        logger.warning(f"Failed to encrypt field {key}: {e}")
        
        return result
    
    @classmethod
    def decrypt_dict(cls, data_dict: dict, keys_to_decrypt: list = None) -> dict:
        """
        Decrypt specific keys in a dictionary.
        
        Args:
            data_dict: Dictionary to process
            keys_to_decrypt: List of keys to decrypt (if None, decrypts all encrypted values)
            
        Returns:
            Dictionary with decrypted values
        """
        if keys_to_decrypt is None:
            # Default sensitive keys
            keys_to_decrypt = [
                'api_key', 'secret', 'password', 'private_key', 'token',
                'jwt_secret', 'encryption_key', 'wallet_key', 'credentials'
            ]
        
        result = data_dict.copy()
        
        for key, value in result.items():
            # Check if key contains sensitive terms and value is encrypted
            should_decrypt = any(sensitive in key.lower() for sensitive in keys_to_decrypt)
            
            if should_decrypt and value and isinstance(value, str) and cls.is_encrypted(value):
                try:
                    result[key] = cls.decrypt_data(value)
                    logger.debug(f"Decrypted field: {key}")
                except Exception as e:
                    logger.warning(f"Failed to decrypt field {key}: {e}")
                    # Keep original value if decryption fails
        
        return result
    
    @classmethod
    def set_master_key(cls, key: str):
        """
        Set the master encryption key.
        
        Args:
            key: Master key for encryption
        """
        cls._master_key = key
        cls._fernet = None  # Reset fernet to use new key
        logger.info("Master encryption key updated")
    
    @classmethod
    def rotate_key(cls, old_data: dict, new_key: str) -> dict:
        """
        Rotate encryption key by decrypting with old key and re-encrypting with new key.
        
        Args:
            old_data: Dictionary with data encrypted with old key
            new_key: New encryption key
            
        Returns:
            Dictionary with data re-encrypted with new key
        """
        # Decrypt with current key
        decrypted_data = cls.decrypt_dict(old_data)
        
        # Set new key
        old_key = cls._master_key
        cls.set_master_key(new_key)
        
        try:
            # Re-encrypt with new key
            re_encrypted_data = cls.encrypt_dict(decrypted_data)
            logger.info("Successfully rotated encryption key")
            return re_encrypted_data
        except Exception as e:
            # Restore old key if rotation fails
            cls.set_master_key(old_key)
            logger.error(f"Key rotation failed, restored old key: {e}")
            raise

class EncryptionError(Exception):
    """Exception raised for encryption/decryption errors."""
    pass

# Utility functions for easy access
def encrypt(data: str) -> str:
    """Convenience function to encrypt data."""
    return EncryptionService.encrypt_data(data)

def decrypt(encrypted_data: str) -> str:
    """Convenience function to decrypt data."""
    return EncryptionService.decrypt_data(encrypted_data)

def is_encrypted(data: str) -> bool:
    """Convenience function to check if data is encrypted."""
    return EncryptionService.is_encrypted(data) 