from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from loguru import logger

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings - remove the constant and use settings instead
# ALGORITHM = "HS256"


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
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
    
    # Convert to timestamp for consistent handling with jwt library
    # Use seconds instead of integer for better datetime compatibility
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating JWT token: {str(e)}")
        raise


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
    Encrypt sensitive data with AES-256.
    This is a placeholder - a real implementation would use a proper encryption library.
    
    Args:
        data: Data to encrypt
        
    Returns:
        Encrypted data
    """
    # In a real implementation, use something like Fernet from cryptography
    # For now, this is just a placeholder
    return f"encrypted:{data}"


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive data.
    This is a placeholder - a real implementation would use a proper encryption library.
    
    Args:
        encrypted_data: Data to decrypt
        
    Returns:
        Decrypted data
    """
    # In a real implementation, use something like Fernet from cryptography
    # For now, this is just a placeholder
    if encrypted_data.startswith("encrypted:"):
        return encrypted_data[10:]
    return encrypted_data 