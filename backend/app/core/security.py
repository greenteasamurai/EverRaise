from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
import secrets
import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from jose import jwt, JWTError
from passlib.context import CryptContext
from loguru import logger

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize encryption for sensitive data
def generate_encryption_key(master_key: str, salt: bytes = None) -> bytes:
    """
    Generate a secure encryption key from a master key using PBKDF2.
    
    Args:
        master_key: Master encryption key
        salt: Salt for key derivation
        
    Returns:
        Fernet-compatible key
    """
    if not salt:
        salt = secrets.token_bytes(16)
        
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    return key

# Global encryption key
ENCRYPTION_KEY = generate_encryption_key(settings.ENCRYPTION_KEY)
fernet = Fernet(ENCRYPTION_KEY)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token with improved security.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
        "nbf": datetime.utcnow(),  # Not valid before
        "jti": secrets.token_hex(16)  # JWT ID for one-time use
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating JWT token: {str(e)}")
        raise


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid
    """
    return jwt.decode(
        token, 
        settings.SECRET_KEY, 
        algorithms=[settings.ALGORITHM],
        options={"verify_signature": True, "verify_exp": True}
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain password
        hashed_password: Hashed password
        
    Returns:
        True if the password is valid
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def encrypt_data(data: str) -> str:
    """
    Encrypt sensitive data with Fernet symmetric encryption (AES-256).
    
    Args:
        data: Data to encrypt
        
    Returns:
        Encrypted data
    """
    if not data:
        return data
        
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive data.
    
    Args:
        encrypted_data: Data to decrypt
        
    Returns:
        Decrypted data
    """
    if not encrypted_data:
        return encrypted_data
        
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logger.error(f"Failed to decrypt data: {str(e)}")
        return "[Decryption Error]"


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Token length
        
    Returns:
        Secure token
    """
    return secrets.token_urlsafe(length)


def hash_email(email: str) -> str:
    """
    Create a secure hash of an email address for pseudonymization.
    
    Args:
        email: Email to hash
        
    Returns:
        Hashed email
    """
    import hashlib
    # Add salt to prevent rainbow table attacks
    salted = f"{email}{settings.SECRET_KEY}"
    return hashlib.sha256(salted.encode()).hexdigest()


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength against security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Dict with validation results
    """
    import re
    
    results = {
        "valid": True,
        "errors": []
    }
    
    # Check length
    if len(password) < 8:
        results["valid"] = False
        results["errors"].append("Password must be at least 8 characters long")
    
    # Check uppercase
    if not re.search(r'[A-Z]', password):
        results["valid"] = False
        results["errors"].append("Password must contain at least one uppercase letter")
    
    # Check lowercase
    if not re.search(r'[a-z]', password):
        results["valid"] = False
        results["errors"].append("Password must contain at least one lowercase letter")
    
    # Check digits
    if not re.search(r'\d', password):
        results["valid"] = False
        results["errors"].append("Password must contain at least one digit")
    
    # Check special characters
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        results["valid"] = False
        results["errors"].append("Password must contain at least one special character")
    
    return results


def is_token_about_to_expire(token: str, threshold_minutes: int = 5) -> bool:
    """
    Check if a JWT token is about to expire.
    
    Args:
        token: JWT token to check
        threshold_minutes: Minutes threshold before expiration
        
    Returns:
        True if token will expire soon
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_signature": True, "verify_exp": False}
        )
        
        if "exp" in payload:
            exp_time = datetime.fromtimestamp(payload["exp"])
            time_left = exp_time - datetime.utcnow()
            return time_left < timedelta(minutes=threshold_minutes)
            
        return True  # No expiration found, consider it expiring
        
    except JWTError:
        return True  # Invalid token, consider it expiring 