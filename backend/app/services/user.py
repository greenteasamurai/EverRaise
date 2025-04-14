from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.schemas.user import UserCreate, UserCreateOAuth, UserUpdate


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email.
    
    Args:
        db: Database session
        email: Email of the user to retrieve
        
    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        user_id: ID of the user to retrieve
        
    Returns:
        User object if found, None otherwise
    """
    return await db.get(User, user_id)


async def get_users(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100, 
    filters: Optional[Dict[str, Any]] = None
) -> List[User]:
    """
    Get a list of users with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Max number of records to return
        filters: Optional filters to apply
        
    Returns:
        List of User objects
    """
    query = select(User)
    
    # Apply filters if provided
    if filters:
        if "is_active" in filters:
            query = query.filter(User.is_active == filters["is_active"])
        if "is_superuser" in filters:
            query = query.filter(User.is_superuser == filters["is_superuser"])
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def create_user(db: AsyncSession, obj_in: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        obj_in: User creation data
        
    Returns:
        Created User object
    """
    # Check that passwords match
    if obj_in.password != obj_in.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
    
    # Create user object
    db_obj = User(
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        first_name=obj_in.first_name,
        last_name=obj_in.last_name,
        is_active=obj_in.is_active if obj_in.is_active is not None else True,
        is_superuser=False,  # Only admins can create superusers
        avatar_url=obj_in.avatar_url,
        notification_email=obj_in.notification_email if obj_in.notification_email is not None else True,
        notification_slack=obj_in.notification_slack if obj_in.notification_slack is not None else True,
    )
    
    # Add to database
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    return db_obj


async def create_oauth_user(db: AsyncSession, obj_in: UserCreateOAuth) -> User:
    """
    Create a new user from OAuth data.
    
    Args:
        db: Database session
        obj_in: OAuth user creation data
        
    Returns:
        Created User object
    """
    # Create user object without password
    db_obj = User(
        email=obj_in.email,
        first_name=obj_in.first_name,
        last_name=obj_in.last_name,
        is_active=True,
        is_superuser=False,
        avatar_url=obj_in.avatar_url,
    )
    
    # Set OAuth provider details
    if obj_in.oauth_provider == "google":
        db_obj.google_id = obj_in.oauth_id
    elif obj_in.oauth_provider == "microsoft":
        db_obj.microsoft_id = obj_in.oauth_id
    elif obj_in.oauth_provider == "slack":
        db_obj.slack_id = obj_in.oauth_id
    
    # Add to database
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    return db_obj


async def update_user(
    db: AsyncSession, 
    *, 
    db_obj: User, 
    obj_in: Union[UserUpdate, Dict[str, Any]]
) -> User:
    """
    Update a user.
    
    Args:
        db: Database session
        db_obj: Existing user object
        obj_in: New user data
        
    Returns:
        Updated User object
    """
    # Convert to dict if not already
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    # Update fields
    for field in update_data:
        if field in update_data and hasattr(db_obj, field):
            setattr(db_obj, field, update_data[field])
    
    # Save to database
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    return db_obj


async def delete_user(db: AsyncSession, *, db_obj: User) -> User:
    """
    Delete a user (soft delete by setting is_active=False).
    
    Args:
        db: Database session
        db_obj: User object to delete
        
    Returns:
        Deleted User object
    """
    # Soft delete
    db_obj.is_active = False
    
    # Save to database
    db.add(db_obj)
    await db.commit()
    
    return db_obj


async def authenticate(
    db: AsyncSession, *, email: str, password: str
) -> Optional[User]:
    """
    Authenticate a user.
    
    Args:
        db: Database session
        email: User email
        password: User password
        
    Returns:
        User object if authentication is successful, None otherwise
    """
    user = await get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user 