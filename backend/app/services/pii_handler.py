import json
import secrets
import re
from typing import Any, Dict, List, Optional, Union, Set, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings

# Initialize encryption key
def generate_key(master_key: str, salt: bytes = None) -> bytes:
    """
    Generate a Fernet key from a master key using PBKDF2.
    
    Args:
        master_key: Master encryption key
        salt: Salt for key derivation (generated if not provided)
        
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


# Create encryption key from settings
ENCRYPTION_KEY = generate_key(settings.ENCRYPTION_KEY)
fernet = Fernet(ENCRYPTION_KEY)

# PII field patterns for detection
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "credit_card": r'\b(\d{4}[- ]){3}\d{4}|\d{16}\b',
    "address": r'\b\d+\s+([A-Za-z]+\s+){1,5},\s+[A-Za-z]+,\s+[A-Z]{2}\s+\d{5}\b',
    "date_of_birth": r'\b(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/(19|20)\d{2}\b'
}

# Known PII field names for structured data
PII_FIELD_NAMES = {
    "email", "email_address", "emailaddress", 
    "phone", "phone_number", "phonenumber", "mobile", "cell",
    "ssn", "social_security", "social_security_number",
    "dob", "date_of_birth", "birthdate", "birth_date",
    "address", "street_address", "home_address", "mailing_address",
    "passport", "passport_number", "passport_id",
    "driver_license", "drivers_license", "driver_license_number",
    "credit_card", "credit_card_number", "cc_number", "card_number",
    "bank_account", "account_number", "bank_account_number",
    "tax_id", "tax_id_number",
    "first_name", "last_name", "full_name", "name",
    "zip", "zip_code", "postal_code", "postcode",
    "city", "state", "country"
}


def encrypt_pii(data: str) -> str:
    """
    Encrypt PII data using Fernet symmetric encryption.
    
    Args:
        data: Data to encrypt
        
    Returns:
        Encrypted data as a string
    """
    if not data:
        return data
        
    return fernet.encrypt(data.encode()).decode()


def decrypt_pii(encrypted_data: str) -> str:
    """
    Decrypt PII data that was encrypted with encrypt_pii.
    
    Args:
        encrypted_data: Encrypted data string
        
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


def mask_pii(data: str, mask_char: str = "*", visible_chars: int = 2) -> str:
    """
    Mask PII by showing only a few characters and replacing the rest.
    
    Args:
        data: PII string to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to show at beginning and end
        
    Returns:
        Masked string
    """
    if not data or len(data) <= visible_chars * 2:
        return data
        
    # For emails, handle specially to preserve domain
    if '@' in data:
        username, domain = data.split('@', 1)
        if len(username) <= visible_chars * 2:
            masked_username = username
        else:
            masked_username = username[:visible_chars] + mask_char * (len(username) - visible_chars * 2) + username[-visible_chars:]
        return f"{masked_username}@{domain}"
    
    # For other PII
    return data[:visible_chars] + mask_char * (len(data) - visible_chars * 2) + data[-visible_chars:]


def detect_pii(text: str) -> Dict[str, List[str]]:
    """
    Detect potential PII in unstructured text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary of PII type and matched values
    """
    if not text:
        return {}
        
    results = {}
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            results[pii_type] = matches
            
    return results


def is_pii_field(field_name: str) -> bool:
    """
    Check if a field name likely contains PII.
    
    Args:
        field_name: Field name to check
        
    Returns:
        True if field likely contains PII
    """
    field_lower = field_name.lower()
    
    # Check against known PII fields
    for pii_field in PII_FIELD_NAMES:
        if pii_field in field_lower:
            return True
            
    return False


def sanitize_dict(data: Dict[str, Any], redact: bool = False, mask: bool = True) -> Dict[str, Any]:
    """
    Sanitize a dictionary by masking or removing PII.
    
    Args:
        data: Dictionary to sanitize
        redact: Whether to completely remove PII fields
        mask: Whether to mask PII values instead of removing
        
    Returns:
        Sanitized dictionary
    """
    if not data:
        return data
        
    result = {}
    
    for key, value in data.items():
        # Check if this is a PII field
        if is_pii_field(key):
            if redact:
                # Skip this field entirely
                continue
            elif mask and isinstance(value, str):
                # Mask the value
                result[key] = mask_pii(value)
            else:
                # Replace with placeholder
                result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            # Recursively process nested dictionaries
            result[key] = sanitize_dict(value, redact, mask)
        elif isinstance(value, list):
            # Process lists
            if all(isinstance(item, dict) for item in value):
                # List of dictionaries
                result[key] = [sanitize_dict(item, redact, mask) for item in value]
            else:
                # Regular list, just include it
                result[key] = value
        else:
            # Regular field, include as is
            result[key] = value
            
    return result


def sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize data for safe logging, removing all PII.
    
    Args:
        data: Data to sanitize
        
    Returns:
        Sanitized data safe for logging
    """
    return sanitize_dict(data, redact=True)


def sanitize_for_ai_processing(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize data for AI processing, masking all PII.
    
    Args:
        data: Data to sanitize
        
    Returns:
        Sanitized data with masked PII
    """
    return sanitize_dict(data, redact=False, mask=True)


class PIIHandler:
    """Class to handle PII data in the application."""
    
    @staticmethod
    async def encrypt_user_pii(db: AsyncSession, user_id: int, pii_data: Dict[str, str]) -> bool:
        """
        Encrypt and store user PII in the database.
        
        Args:
            db: Database session
            user_id: User ID
            pii_data: Dictionary of PII to encrypt and store
            
        Returns:
            Success status
        """
        # This is a placeholder for actual implementation
        # In a real implementation, you would:
        # 1. Encrypt each PII field
        # 2. Store in a dedicated PII table with user_id reference
        # 3. Apply appropriate access controls
        
        try:
            encrypted_data = {k: encrypt_pii(v) for k, v in pii_data.items()}
            # TODO: Store encrypted_data in database
            logger.info(f"PII data encrypted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to encrypt user PII: {str(e)}")
            return False
    
    @staticmethod
    async def get_user_pii(db: AsyncSession, user_id: int, fields: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Retrieve and decrypt user PII from the database.
        
        Args:
            db: Database session
            user_id: User ID
            fields: Specific PII fields to retrieve (all if None)
            
        Returns:
            Dictionary of decrypted PII
        """
        # This is a placeholder for actual implementation
        # In a real implementation, you would:
        # 1. Retrieve encrypted PII from database
        # 2. Decrypt each field
        # 3. Log access for audit purposes
        
        # TODO: Implement actual retrieval and decryption
        logger.info(f"PII data retrieved and decrypted for user {user_id}")
        return {}
    
    @staticmethod
    def log_pii_access(user_id: int, accessed_by: int, fields: List[str], purpose: str) -> None:
        """
        Log PII access for audit purposes.
        
        Args:
            user_id: User whose PII was accessed
            accessed_by: User who accessed the PII
            fields: PII fields that were accessed
            purpose: Purpose for accessing PII
        """
        # In a production system, this would write to a secure audit log
        logger.info(
            f"PII ACCESS: User {accessed_by} accessed {', '.join(fields)} "
            f"for user {user_id} for purpose: {purpose}"
        )
    
    @staticmethod
    def prepare_external_data(data: Dict[str, Any], context: str = "api") -> Dict[str, Any]:
        """
        Prepare data for external consumption by sanitizing PII.
        
        Args:
            data: Data to prepare
            context: Context for preparation (api, report, etc.)
            
        Returns:
            Sanitized data
        """
        if context == "ai-processing":
            return sanitize_for_ai_processing(data)
        elif context == "logging":
            return sanitize_for_logging(data)
        else:
            # For API responses, mask sensitive PII but keep identifiers
            return sanitize_dict(data, redact=False, mask=True)
            
    @staticmethod
    def detect_pii_in_text(text: str) -> Dict[str, List[str]]:
        """
        Detect PII in unstructured text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of detected PII
        """
        return detect_pii(text)
    
    @staticmethod
    def is_compliant_for_storage(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if data complies with PII storage policies.
        
        Args:
            data: Data to check
            
        Returns:
            Tuple of (is_compliant, list_of_violations)
        """
        violations = []
        
        # Check for unencrypted PII in inappropriate fields
        for key, value in data.items():
            if is_pii_field(key) and isinstance(value, str) and not value.startswith("gAAAAAB"):
                violations.append(f"Unencrypted PII in field: {key}")
        
        return len(violations) == 0, violations 