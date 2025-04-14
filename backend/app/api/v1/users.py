from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.api.deps import get_current_active_superuser, get_current_user, get_db
from app.core.security import get_password_hash
from app.db.models.user import User
from app.db.models.organization import Organization
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return [UserResponse.model_validate(user) for user in users]

@router.post("/", response_model=UserResponse, status_code=HTTP_201_CREATED)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate = Body(...),
) -> Any:
    """
    Create new user and associate with an organization.
    """
    # Check if the email already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    # Verify passwords match
    if user_in.password != user_in.password_confirm:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
    
    # Fetch the organization
    org_result = await db.execute(select(Organization).where(Organization.id == user_in.organization_id))
    organization = org_result.scalars().first()
    if not organization:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {user_in.organization_id} not found.",
        )

    # Create user object
    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        is_active=True,
        is_superuser=False,
    )
    
    # Associate with organization
    db_user.organizations.append(organization)
    
    db.add(db_user)
    try:
        # Commit saves user and the association
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        # More specific error might be helpful depending on the cause
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error during user creation: {e}", 
        )
    await db.refresh(db_user)
    return UserResponse.model_validate(db_user)

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    # Only allow superusers to view other users
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to access this user"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int = Path(...),
    user_in: UserUpdate = Body(...),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a user.
    """
    # Only allow users to update themselves or superusers to update anyone
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to update this user"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update user data
    user_data = user_in.dict(exclude_unset=True)
    
    # Handle password hashing if provided
    if "password" in user_data and user_data["password"]:
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    
    # Update user attributes
    for field, value in user_data.items():
        if hasattr(user, field) and value is not None:
            setattr(user, field, value)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int = Path(...),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Delete a user.
    """
    print(f"DEBUG: Attempting to delete user with id {user_id}")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    print(f"DEBUG: Delete user search result: {user}")
    
    if not user:
        print(f"DEBUG: User with id {user_id} not found in the database")
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Soft delete by setting is_active to False
    user.is_active = False
    db.add(user)
    await db.commit()
    
    print(f"DEBUG: User {user.email} (id: {user.id}) was successfully soft-deleted")
    return UserResponse.model_validate(user) 