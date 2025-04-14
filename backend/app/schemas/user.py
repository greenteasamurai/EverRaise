from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, constr


# Shared properties
class UserBase(BaseModel):
    """
    Base class for user schemas with shared properties.
    """
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = True
    avatar_url: Optional[str] = None
    notification_email: Optional[bool] = True
    notification_slack: Optional[bool] = True


# Properties to receive on user creation
class UserCreate(UserBase):
    """
    Schema for creating a new user.
    """
    email: EmailStr
    password: constr(min_length=8)
    password_confirm: constr(min_length=8)
    organization_id: int


class UserCreateOAuth(UserBase):
    """
    Schema for creating a new user with OAuth.
    """
    email: EmailStr
    oauth_provider: str
    oauth_id: str


# Properties to receive on user update
class UserUpdate(UserBase):
    """
    Schema for updating an existing user.
    """
    password: Optional[constr(min_length=8)] = None


# Properties stored in DB
class UserInDB(UserBase):
    """
    Schema representing a user as stored in the database.
    """
    id: int
    email: EmailStr
    hashed_password: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    
    # OAuth fields
    google_id: Optional[str] = None
    microsoft_id: Optional[str] = None
    slack_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Properties to return via API
class UserResponse(UserBase):
    """
    Schema for user data in API responses.
    """
    id: int
    email: EmailStr
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    # OAuth flags (but not IDs for security)
    has_google: bool = False
    has_microsoft: bool = False
    has_slack: bool = False
    
    @classmethod
    def model_validate(cls, user):
        """
        Create a UserResponse from an ORM User model.
        """
        return cls(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            avatar_url=user.avatar_url,
            notification_email=user.notification_email,
            notification_slack=user.notification_slack,
            created_at=user.created_at,
            has_google=bool(user.google_id),
            has_microsoft=bool(user.microsoft_id),
            has_slack=bool(user.slack_id),
        )


# Properties for user list responses
class UserListResponse(BaseModel):
    """
    Schema for lists of users in API responses.
    """
    users: List[UserResponse]
    total: int
    page: int
    page_size: int 