import pytest
import time
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.core.config import settings
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    encrypt_data,
    decrypt_data
)
from app.schemas.auth import TokenPayload

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

@pytest.mark.unit
class TestSecurityUtils:
    """Tests for security utility functions."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        # Test password hashing
        password = "secretpassword"
        hashed_password = get_password_hash(password)
        
        # Verify the hash is different from the original password
        assert hashed_password != password
        assert isinstance(hashed_password, str)
        
        # Test password verification
        assert verify_password(password, hashed_password) is True
        assert verify_password("wrongpassword", hashed_password) is False
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        # Test data
        user_id = "testuser"
        data = {"sub": user_id}
        
        # Create token with default expiry
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token without checking expiry
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        assert payload["sub"] == user_id
        assert "exp" in payload
        
        # Create token with custom expiry
        expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token_with_expiry = create_access_token(data, expires_delta=expires)
        
        # Decode and verify custom expiry token without checking expiry
        payload = jwt.decode(token_with_expiry, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        assert payload["sub"] == user_id
        
        # Verify token can be decoded with expiry check, which means it's not expired
        jwt.decode(token_with_expiry, SECRET_KEY, algorithms=[ALGORITHM])
    
    def test_token_expiry(self):
        """Test token expiration."""
        user_id = "testuser"
        # Create a token that expires very quickly (1 millisecond)
        expires = timedelta(milliseconds=1)
        token = create_access_token({"sub": user_id}, expires_delta=expires)
        
        # Wait slightly longer than the expiry time
        time.sleep(1.0) # Increased sleep time to 1.0s for maximum robustness
        
        # The token should be expired now, so decoding should raise JWTError (specifically ExpiredSignatureError)
        with pytest.raises(JWTError): # Catching JWTError is broader but safer
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    def test_encryption_functions(self):
        """Test the data encryption and decryption functions."""
        # Test data
        sensitive_data = "sensitive-info-123"
        
        # Test encryption
        encrypted = encrypt_data(sensitive_data)
        assert encrypted != sensitive_data
        assert "encrypted:" in encrypted
        
        # Test decryption
        decrypted = decrypt_data(encrypted)
        assert decrypted == sensitive_data
        
        # Test decryption with non-encrypted data
        non_encrypted = "regular-data"
        assert decrypt_data(non_encrypted) == non_encrypted

    def test_invalid_token(self):
        # Test decoding a malformed token
        with pytest.raises(JWTError):
            jwt.decode("invalid.token.string", SECRET_KEY, algorithms=[ALGORITHM])
            
        # Test decoding with wrong secret key
        token = create_access_token({"sub": "testuser"})
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret", algorithms=[ALGORITHM])
            
        # Test decoding with wrong algorithm
        with pytest.raises(JWTError):
            jwt.decode(token, SECRET_KEY, algorithms=["HS512"]) 