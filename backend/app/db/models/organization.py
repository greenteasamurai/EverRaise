from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.db.base_class import Base
from app.db.models.user import user_organization


class IntegrationType(str, PyEnum):
    """
    Supported integration types.
    """
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    SLACK = "slack"
    TEAMS = "teams"
    JIRA = "jira"
    ASANA = "asana"
    NOTION = "notion"
    GDRIVE = "gdrive"
    DROPBOX = "dropbox"
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    TABLEAU = "tableau"


class Organization(Base):
    """
    Organization model for multi-tenancy.
    """
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(255), nullable=True)
    is_active = Column(Boolean(), default=True)
    
    # Subscription information
    plan_tier = Column(String(50), default="free")  # free, pro, enterprise
    subscription_id = Column(String(255), nullable=True)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_organization,
        back_populates="organizations",
    )
    
    integrations: Mapped[List["Integration"]] = relationship(
        "Integration",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<Organization {self.name}>"


class Integration(Base):
    """
    Model for storing API integrations for data sources.
    """
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False)
    type = Column(Enum(IntegrationType), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Connection status
    is_active = Column(Boolean(), default=True)
    last_sync_at = Column(String(255), nullable=True)
    
    # Encrypted credentials
    credentials = Column(Text, nullable=True)  # Encrypted JSON string
    refresh_token = Column(Text, nullable=True)
    access_token = Column(Text, nullable=True)
    
    # Configuration
    config = Column(Text, nullable=True)  # JSON configuration
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="integrations",
    )
    
    data_sources: Mapped[List["DataSource"]] = relationship(
        "DataSource",
        back_populates="integration",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<Integration {self.name} ({self.type})>"


class DataSource(Base):
    """
    Model for storing individual data sources from integrations.
    Examples: A specific Slack channel, Gmail label, or Jira project.
    """
    integration_id = Column(Integer, ForeignKey("integration.id"), nullable=False)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # channel, label, project, etc.
    source_id = Column(String(255), nullable=False)  # External ID
    
    # Source-specific configuration
    config = Column(Text, nullable=True)  # JSON configuration
    
    # Sync status
    is_active = Column(Boolean(), default=True)
    last_sync_at = Column(String(255), nullable=True)
    
    # Relationship to integration
    integration: Mapped["Integration"] = relationship(
        "Integration",
        back_populates="data_sources",
    )
    
    def __repr__(self):
        return f"<DataSource {self.name} ({self.source_type})>" 