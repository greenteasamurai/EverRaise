from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from sqlalchemy.future import select

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models.user import User
from app.schemas.auth import AuthResponse, Token, TokenPayload, LoginRequest, PasswordResetRequest
from app.schemas.user import UserCreate, UserInDB, UserResponse
from app.services.user import create_user, get_user_by_email

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Handles form data (username, password).
    """
    # Find the user by email (using form_data.username as email)
    stmt = select(User).where(User.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login attempt failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user account is active
    if not user.is_active:
        logger.warning(f"Inactive user tried to login: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    
    # Create access token with user information (use user.email and user.id)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}, 
        expires_delta=access_token_expires,
    )
    
    logger.info(f"User logged in successfully: {user.email}")
    
    # Return token and user information
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/register", response_model=AuthResponse)
async def register(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register a new user.
    """
    # Check if user already exists
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Create new user
    user = await create_user(db, obj_in=user_in)
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Refresh access token.
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.email, "user_id": current_user.id},
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout() -> Dict[str, str]:
    """
    Logout - client-side only, the token must be discarded by the client.
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user information.
    """
    return current_user


@router.post("/password-reset-request")
async def request_password_reset(
    request_data: PasswordResetRequest = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Request a password reset link for a user identified by email.
    Generates a reset token and sends it via email (implementation pending).
    Returns 200 OK even if user not found to prevent email enumeration.
    """
    logger.info(f"Password reset requested for email: {request_data.email}")
    user = await get_user_by_email(db, email=request_data.email)

    if not user:
        # Don't reveal that the user doesn't exist
        logger.warning(f"Password reset requested for non-existent user: {request_data.email}")
        # TODO: Potentially add a small delay here to make timing attacks harder
    else:
        # TODO: Generate password reset token
        # reset_token = create_password_reset_token(email=user.email)
        reset_token = "dummy_reset_token" # Placeholder
        logger.info(f"Generated password reset token for user: {user.email}")

        # TODO: Send email with the reset token/link
        # await send_password_reset_email(email_to=user.email, token=reset_token)
        logger.info(f"Simulating sending password reset email to: {user.email} with token: {reset_token}")

    # Always return success to prevent user enumeration
    return {"message": "If an account with that email exists, a password reset link has been sent."}


# OAuth endpoints would go here, but they require complex setup with providers
@router.get("/oauth/google")
async def login_google() -> Dict[str, str]:
    """
    Google OAuth login (placeholder).
    """
    return {"message": "Google OAuth endpoint - implementation required"}


@router.get("/oauth/microsoft")
async def login_microsoft() -> Dict[str, str]:
    """
    Microsoft OAuth login (placeholder).
    """
    return {"message": "Microsoft OAuth endpoint - implementation required"}


@router.get("/oauth/slack")
async def login_slack() -> Dict[str, str]:
    """
    Slack OAuth login (placeholder).
    """
    return {"message": "Slack OAuth endpoint - implementation required"} 