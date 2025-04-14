from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from sqlalchemy.future import select
from fastapi.responses import RedirectResponse

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password, validate_password_strength
from app.db.models.user import User
from app.schemas.auth import (
    AuthResponse, Token, TokenPayload, LoginRequest, PasswordResetRequest,
    GoogleOAuthRequest, MicrosoftOAuthRequest, SlackOAuthRequest, OAuth2TokenExchangeRequest
)
from app.schemas.user import UserCreate, UserInDB, UserResponse
from app.services.user import create_user, get_user_by_email
from app.services.oauth import (
    get_authorization_url, process_oauth_callback, revoke_oauth_access
)
from app.services.pii_handler import PIIHandler

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Handles form data (username, password).
    """
    # Find the user by email (using form_data.username as email)
    stmt = select(User).where(User.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login attempt failed for user: {form_data.username} from {client_ip} ({user_agent})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user account is active
    if not user.is_active:
        logger.warning(f"Inactive user tried to login: {form_data.username} from {client_ip} ({user_agent})")
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
    
    logger.info(f"User logged in successfully: {user.email} from {client_ip} ({user_agent})")
    
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
    request: Request = None,
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
    
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    # Validate password strength
    if user_in.password != user_in.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
    
    password_validation = validate_password_strength(user_in.password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"password_errors": password_validation["errors"]},
        )
    
    # Create new user
    user = await create_user(db, obj_in=user_in)
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    
    logger.info(f"New user registered: {user.email} from {client_ip} ({user_agent})")
    
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
    
    logger.info(f"Token refreshed for user: {current_user.email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(request: Request = None) -> Dict[str, str]:
    """
    Logout - client-side only, the token must be discarded by the client.
    In a production app, you might want to invalidate the token server-side
    by adding it to a blacklist in Redis or similar.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    logger.info(f"User logged out from {client_ip} ({user_agent})")
    
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
    request: Request = None,
) -> Dict[str, str]:
    """
    Request a password reset link for a user identified by email.
    Generates a reset token and sends it via email (implementation pending).
    Returns 200 OK even if user not found to prevent email enumeration.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    logger.info(f"Password reset requested for email: {request_data.email} from {client_ip} ({user_agent})")
    user = await get_user_by_email(db, email=request_data.email)

    if not user:
        # Don't reveal that the user doesn't exist
        logger.warning(f"Password reset requested for non-existent user: {request_data.email} from {client_ip}")
        # Add a small delay to make timing attacks harder
        import asyncio
        await asyncio.sleep(1)
    else:
        # Generate password reset token
        reset_token_expires = timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        reset_token = create_access_token(
            data={"sub": user.email, "type": "password_reset"},
            expires_delta=reset_token_expires,
        )
        
        # TODO: Implement email sending functionality
        reset_url = f"{settings.SERVER_HOST}/reset-password?token={reset_token}"
        logger.info(f"Generated password reset token for user: {user.email}")
        logger.info(f"Password reset URL: {reset_url}")

    # Always return success to prevent user enumeration
    return {"message": "If an account with that email exists, a password reset link has been sent."}


# OAuth authorization URL endpoints
@router.get("/oauth/google/authorize")
async def authorize_google(
    redirect_uri: str = Query(..., description="Redirect URI after authorization"),
) -> Dict[str, str]:
    """
    Get Google OAuth authorization URL.
    """
    authorization_url = get_authorization_url("google", redirect_uri)
    return {"authorization_url": authorization_url}


@router.get("/oauth/microsoft/authorize")
async def authorize_microsoft(
    redirect_uri: str = Query(..., description="Redirect URI after authorization"),
) -> Dict[str, str]:
    """
    Get Microsoft OAuth authorization URL.
    """
    authorization_url = get_authorization_url("microsoft", redirect_uri)
    return {"authorization_url": authorization_url}


@router.get("/oauth/slack/authorize")
async def authorize_slack(
    redirect_uri: str = Query(..., description="Redirect URI after authorization"),
) -> Dict[str, str]:
    """
    Get Slack OAuth authorization URL.
    """
    authorization_url = get_authorization_url("slack", redirect_uri)
    return {"authorization_url": authorization_url}


# OAuth callback endpoints
@router.get("/oauth/google/callback")
async def google_oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="OAuth state parameter"),
    redirect_uri: str = Query(..., description="Redirect URI used in the authorization request"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> RedirectResponse:
    """
    Handle Google OAuth callback.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    try:
        # Process OAuth callback
        auth_result = await process_oauth_callback(db, "google", code, redirect_uri, state)
        
        # Create frontend redirect URL with token
        frontend_redirect = f"{redirect_uri.split('/auth/')[0]}?token={auth_result['access_token']}"
        
        logger.info(f"Google OAuth successful for user: {auth_result['user'].email} from {client_ip}")
        
        # Return URL that frontend will use to extract token
        return RedirectResponse(url=frontend_redirect)
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)} from {client_ip} ({user_agent})")
        # Redirect to error page
        return RedirectResponse(url=f"{redirect_uri.split('/auth/')[0]}/auth/error?error={str(e)}")


@router.get("/oauth/microsoft/callback")
async def microsoft_oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="OAuth state parameter"),
    redirect_uri: str = Query(..., description="Redirect URI used in the authorization request"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> RedirectResponse:
    """
    Handle Microsoft OAuth callback.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    try:
        # Process OAuth callback
        auth_result = await process_oauth_callback(db, "microsoft", code, redirect_uri, state)
        
        # Create frontend redirect URL with token
        frontend_redirect = f"{redirect_uri.split('/auth/')[0]}?token={auth_result['access_token']}"
        
        logger.info(f"Microsoft OAuth successful for user: {auth_result['user'].email} from {client_ip}")
        
        # Return URL that frontend will use to extract token
        return RedirectResponse(url=frontend_redirect)
    except Exception as e:
        logger.error(f"Microsoft OAuth error: {str(e)} from {client_ip} ({user_agent})")
        # Redirect to error page
        return RedirectResponse(url=f"{redirect_uri.split('/auth/')[0]}/auth/error?error={str(e)}")


@router.get("/oauth/slack/callback")
async def slack_oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="OAuth state parameter"),
    redirect_uri: str = Query(..., description="Redirect URI used in the authorization request"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> RedirectResponse:
    """
    Handle Slack OAuth callback.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    try:
        # Process OAuth callback
        auth_result = await process_oauth_callback(db, "slack", code, redirect_uri, state)
        
        # Create frontend redirect URL with token
        frontend_redirect = f"{redirect_uri.split('/auth/')[0]}?token={auth_result['access_token']}"
        
        logger.info(f"Slack OAuth successful for user: {auth_result['user'].email} from {client_ip}")
        
        # Return URL that frontend will use to extract token
        return RedirectResponse(url=frontend_redirect)
    except Exception as e:
        logger.error(f"Slack OAuth error: {str(e)} from {client_ip} ({user_agent})")
        # Redirect to error page
        return RedirectResponse(url=f"{redirect_uri.split('/auth/')[0]}/auth/error?error={str(e)}")


# Token exchange endpoint for client-side OAuth flow
@router.post("/oauth/token", response_model=Token)
async def exchange_oauth_token(
    token_request: OAuth2TokenExchangeRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> Any:
    """
    Exchange OAuth authorization code for access token.
    Used in client-side OAuth flow where the frontend gets the authorization code.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    # Handle a fake state parameter for client-side flow
    # In a real implementation, you'd want to validate this properly
    mock_state = "client_side_flow"
    
    try:
        # Process OAuth callback
        auth_result = await process_oauth_callback(
            db, 
            token_request.provider, 
            token_request.code, 
            token_request.redirect_uri,
            mock_state
        )
        
        logger.info(f"OAuth token exchange successful for user: {auth_result['user'].email} from {client_ip}")
        
        return {
            "access_token": auth_result["access_token"],
            "token_type": "bearer",
            "user": auth_result["user"]
        }
    except Exception as e:
        logger.error(f"OAuth token exchange error: {str(e)} from {client_ip} ({user_agent})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error exchanging OAuth token: {str(e)}"
        )


@router.post("/oauth/revoke/{provider}")
async def revoke_provider_oauth(
    provider: str,
    current_user: User = Depends(get_current_user),
    request: Request = None,
) -> Dict[str, str]:
    """
    Revoke OAuth access for a provider.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    if provider not in ["google", "microsoft", "slack"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    # Check if user has this provider connected
    provider_id_field = f"{provider}_id"
    if not getattr(current_user, provider_id_field, None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You don't have {provider} connected to your account"
        )
    
    # Revoke OAuth access
    success = revoke_oauth_access(current_user, provider)
    
    if success:
        logger.info(f"User {current_user.email} revoked {provider} OAuth access from {client_ip}")
        return {"message": f"Successfully revoked {provider} access"}
    else:
        logger.error(f"Failed to revoke {provider} OAuth access for user {current_user.email} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke {provider} access"
        ) 