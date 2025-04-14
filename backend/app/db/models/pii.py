from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class UserPII(Base):
    """
    Model for storing encrypted PII data separately from the main user table.
    This follows the principle of data minimization and separation of concerns.
    """
    # Reference to the user this PII belongs to
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="pii_data")
    
    # Encrypted PII fields - all stored as encrypted strings
    # Note: These fields may be null if the user hasn't provided this information
    encrypted_address = Column(Text, nullable=True)
    encrypted_phone = Column(String(255), nullable=True)
    encrypted_date_of_birth = Column(String(255), nullable=True)
    encrypted_ssn = Column(String(255), nullable=True)
    encrypted_tax_id = Column(String(255), nullable=True)
    
    # Additional custom PII fields stored as JSON
    # For flexible storage of other PII that doesn't fit in predefined fields
    encrypted_additional_pii = Column(JSON, nullable=True)
    
    # Access tracking
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    access_count = Column(Integer, default=0, nullable=False)
    
    # Consent tracking
    has_consent = Column(Boolean, default=False, nullable=False)
    consent_given_at = Column(DateTime(timezone=True), nullable=True)
    consent_revoked_at = Column(DateTime(timezone=True), nullable=True)
    consent_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit information
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UserPII(user_id={self.user_id})>"


class PIIAccessLog(Base):
    """
    Audit log for PII access.
    Records who accessed what PII data, when, and why.
    """
    # Who accessed the PII
    accessed_by_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    accessed_by = relationship("User", foreign_keys=[accessed_by_id])
    
    # Whose PII was accessed
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", foreign_keys=[user_id])
    
    # What was accessed
    accessed_fields = Column(JSON, nullable=False)  # List of fields accessed
    
    # When and why
    accessed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    access_reason = Column(String(255), nullable=False)
    access_context = Column(String(255), nullable=True)  # API, admin panel, report, etc.
    
    # IP and user agent for audit
    ip_address = Column(String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<PIIAccessLog(user_id={self.user_id}, accessed_by={self.accessed_by_id})>"


class OAuthToken(Base):
    """
    Model for storing encrypted OAuth tokens.
    Separated from the user model for security.
    """
    # Reference to the user these tokens belong to
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="oauth_tokens")
    
    # OAuth provider
    provider = Column(String(50), nullable=False)  # google, microsoft, slack, etc.
    
    # Encrypted tokens
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text, nullable=True)
    
    # Token metadata
    expires_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(String(255), nullable=True)
    
    # Audit information
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # OAuth provider's user ID (kept for reference)
    provider_user_id = Column(String(255), nullable=True)
    
    __table_args__ = (
        # Ensure each user has only one token per provider
        # (Note: In SQLAlchemy, UniqueConstraint would be imported and used here)
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self):
        return f"<OAuthToken(user_id={self.user_id}, provider={self.provider})>"


class DataRetentionPolicy(Base):
    """
    Model for tracking data retention policies by data category.
    Used to automate data deletion after retention period expires.
    """
    # Policy details
    data_category = Column(String(50), nullable=False, unique=True)  # pii, oauth_tokens, etc.
    retention_period_days = Column(Integer, nullable=False)
    require_explicit_consent = Column(Boolean, default=True, nullable=False)
    
    # Policy metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_applied_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit information
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<DataRetentionPolicy(data_category={self.data_category}, days={self.retention_period_days})>" 