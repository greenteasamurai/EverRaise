from typing import List, Optional

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, relationship

from app.db.base_class import Base

# Association table for user-organization many-to-many relationship
user_organization = Table(
    "user_organization",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("organization_id", Integer, ForeignKey("organization.id"), primary_key=True),
    Column("role", String(50), nullable=False, default="member"),  # member, admin, owner
)


class User(Base):
    """
    User model for authentication and authorization.
    """
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)  # nullable for OAuth users
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    
    # OAuth providers
    google_id = Column(String(255), nullable=True, unique=True)
    microsoft_id = Column(String(255), nullable=True, unique=True)
    slack_id = Column(String(255), nullable=True, unique=True)
    
    # Profile picture
    avatar_url = Column(String(255), nullable=True)
    
    # User preferences
    notification_email = Column(Boolean(), default=True)
    notification_slack = Column(Boolean(), default=True)
    
    # Relationships
    organizations: Mapped[List["Organization"]] = relationship(
        "Organization",
        secondary=user_organization,
        back_populates="users",
    )
    
    # Reports created by this user
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="creator",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def full_name(self) -> str:
        """
        Return full name of user.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    @property
    def is_oauth_user(self) -> bool:
        """
        Check if user is authenticated via OAuth.
        """
        return bool(self.google_id or self.microsoft_id or self.slack_id) 