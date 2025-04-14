import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.security import create_access_token, encrypt_data, decrypt_data
from app.db.models.user import User
from app.services.user import get_user_by_email, create_oauth_user, update_user

# Create a Fernet key for encrypting OAuth state and tokens
encryption_key = Fernet.generate_key() if not settings.ENCRYPTION_KEY else settings.ENCRYPTION_KEY.encode()
fernet = Fernet(encryption_key)

# OAuth state dictionary to prevent CSRF attacks
# In production, this should be stored in Redis or another persistent store
oauth_states = {}

# Timeout for OAuth client requests
CLIENT_TIMEOUT = 15.0  # seconds

# OAuth configuration
OAUTH_PROVIDERS = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_info_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "scopes": ["openid", "email", "profile"],
    },
    "microsoft": {
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "user_info_url": "https://graph.microsoft.com/v1.0/me",
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "client_secret": settings.MICROSOFT_CLIENT_SECRET,
        "scopes": ["User.Read", "profile", "email", "openid"],
    },
    "slack": {
        "auth_url": "https://slack.com/oauth/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "user_info_url": "https://slack.com/api/users.identity",
        "client_id": settings.SLACK_CLIENT_ID,
        "client_secret": settings.SLACK_CLIENT_SECRET,
        "scopes": ["identity.basic", "identity.email"],
    },
}


def generate_oauth_state(redirect_uri: str, provider: str) -> str:
    """
    Generate a secure state parameter for OAuth flow.
    
    Args:
        redirect_uri: Where to redirect after auth
        provider: OAuth provider name
        
    Returns:
        Encrypted state token
    """
    # Generate a random state
    state_token = secrets.token_urlsafe(32)
    
    # Store state with metadata
    state_data = {
        "token": state_token,
        "created_at": datetime.utcnow().isoformat(),
        "provider": provider,
        "redirect_uri": redirect_uri
    }
    
    # Encrypt the state data
    encrypted_state = fernet.encrypt(json.dumps(state_data).encode()).decode()
    
    # Store for validation (with expiration of 10 minutes)
    oauth_states[state_token] = {
        "data": state_data,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    
    return encrypted_state


def validate_oauth_state(state: str) -> Tuple[bool, Optional[Dict]]:
    """
    Validate the OAuth state parameter to prevent CSRF attacks.
    
    Args:
        state: The encrypted state from the OAuth callback
        
    Returns:
        Tuple of (is_valid, state_data)
    """
    try:
        # Decrypt the state
        decrypted_data = json.loads(fernet.decrypt(state.encode()).decode())
        state_token = decrypted_data.get("token")
        
        # Check if state exists and hasn't expired
        if state_token in oauth_states:
            stored_state = oauth_states[state_token]
            if datetime.utcnow() < stored_state["expires_at"]:
                # State is valid, remove it to prevent replay attacks
                state_data = stored_state["data"]
                del oauth_states[state_token]
                return True, state_data
        
        return False, None
    except Exception as e:
        logger.warning(f"Error validating OAuth state: {str(e)}")
        return False, None


def get_authorization_url(provider: str, redirect_uri: str) -> str:
    """
    Get the OAuth authorization URL for the specified provider.
    
    Args:
        provider: OAuth provider name
        redirect_uri: Where to redirect after authentication
        
    Returns:
        Authorization URL
    """
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    provider_config = OAUTH_PROVIDERS[provider]
    
    # Generate and store state
    state = generate_oauth_state(redirect_uri, provider)
    
    # Build authorization URL
    params = {
        "client_id": provider_config["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(provider_config["scopes"]),
        "state": state,
        "access_type": "offline",  # Get refresh token (Google)
        "prompt": "consent"  # Force consent screen to get refresh token
    }
    
    # Remove provider-specific params if not applicable
    if provider != "google":
        params.pop("access_type", None)
    
    if provider == "slack":
        params.pop("prompt", None)
    
    return f"{provider_config['auth_url']}?{urlencode(params)}"


async def exchange_code_for_token(
    provider: str, 
    code: str, 
    redirect_uri: str,
    state: str
) -> Dict[str, Any]:
    """
    Exchange OAuth authorization code for tokens.
    
    Args:
        provider: OAuth provider name
        code: Authorization code
        redirect_uri: Redirect URI used in authorization
        state: OAuth state parameter
        
    Returns:
        Dict containing tokens and user info
    """
    # Validate state first to prevent CSRF
    is_valid, state_data = validate_oauth_state(state)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter"
        )
    
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    provider_config = OAUTH_PROVIDERS[provider]
    
    # Exchange code for token
    token_data = await _get_oauth_tokens(provider, code, redirect_uri)
    
    # Get user info with the access token
    user_info = await _get_oauth_user_info(provider, token_data.get("access_token"))
    
    # Combine results
    result = {
        "tokens": token_data,
        "user_info": user_info,
        "provider": provider
    }
    
    return result


async def _get_oauth_tokens(provider: str, code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Get OAuth tokens by exchanging the authorization code.
    
    Args:
        provider: OAuth provider name
        code: Authorization code
        redirect_uri: Redirect URI used in authorization
        
    Returns:
        Dict containing access_token, refresh_token, etc.
    """
    provider_config = OAUTH_PROVIDERS[provider]
    
    # Prepare token request params
    data = {
        "client_id": provider_config["client_id"],
        "client_secret": provider_config["client_secret"],
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    # Make token request
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        try:
            response = await client.post(
                provider_config["token_url"], 
                data=data,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"OAuth token exchange error for {provider}: {str(e)} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error exchanging code for tokens: {str(e)}"
            )
        except Exception as e:
            logger.error(f"OAuth token exchange unexpected error for {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error during OAuth authentication"
            )


async def _get_oauth_user_info(provider: str, access_token: str) -> Dict[str, Any]:
    """
    Get user information from the OAuth provider.
    
    Args:
        provider: OAuth provider name
        access_token: OAuth access token
        
    Returns:
        Dict containing user information
    """
    provider_config = OAUTH_PROVIDERS[provider]
    
    # Set up headers for user info request
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Special handling for Slack
    if provider == "slack":
        headers = {"Authorization": f"Bearer {access_token}"}
    
    # Make user info request
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        try:
            response = await client.get(
                provider_config["user_info_url"],
                headers=headers
            )
            response.raise_for_status()
            
            # Parse response based on provider
            user_data = response.json()
            
            # Normalize user data based on provider
            if provider == "slack":
                # Check if Slack API returned an error
                if not user_data.get("ok", False):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, 
                        detail=f"Slack API error: {user_data.get('error')}"
                    )
                user = user_data.get("user", {})
                return {
                    "id": user.get("id"),
                    "email": user.get("email"),
                    "name": user.get("name"),
                    "avatar": user.get("image_512")
                }
            elif provider == "microsoft":
                return {
                    "id": user_data.get("id"),
                    "email": user_data.get("mail") or user_data.get("userPrincipalName"),
                    "name": user_data.get("displayName"),
                    "first_name": user_data.get("givenName"),
                    "last_name": user_data.get("surname"),
                    "avatar": None  # Microsoft Graph doesn't return an avatar directly
                }
            else:  # Google
                return {
                    "id": user_data.get("sub"),
                    "email": user_data.get("email"),
                    "email_verified": user_data.get("email_verified", False),
                    "name": user_data.get("name"),
                    "first_name": user_data.get("given_name"),
                    "last_name": user_data.get("family_name"),
                    "avatar": user_data.get("picture")
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OAuth user info error for {provider}: {str(e)} - {e.response.text if hasattr(e, 'response') else ''}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error getting user info: {str(e)}"
            )
        except Exception as e:
            logger.error(f"OAuth user info unexpected error for {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error getting user information"
            )


async def process_oauth_callback(
    db: AsyncSession,
    provider: str,
    code: str,
    redirect_uri: str,
    state: str
) -> Dict[str, Any]:
    """
    Process OAuth callback and authenticate/register user.
    
    Args:
        db: Database session
        provider: OAuth provider name
        code: Authorization code
        redirect_uri: Redirect URI used in authorization
        state: OAuth state parameter
        
    Returns:
        Dict with access token and user information
    """
    # Exchange code for tokens and get user info
    oauth_result = await exchange_code_for_token(provider, code, redirect_uri, state)
    user_info = oauth_result["user_info"]
    
    # Validate email
    email = user_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider did not return an email address"
        )
    
    # Check if user already exists
    user = await get_user_by_email(db, email=email)
    
    if user:
        # Update OAuth provider ID if not already set
        provider_id_field = f"{provider}_id"
        oauth_id = user_info.get("id")
        
        update_data = {}
        if oauth_id and not getattr(user, provider_id_field, None):
            update_data[provider_id_field] = oauth_id
        
        # Update avatar if available and not already set
        if user_info.get("avatar") and not user.avatar_url:
            update_data["avatar_url"] = user_info.get("avatar")
            
        # Update name if not already set
        if user_info.get("first_name") and not user.first_name:
            update_data["first_name"] = user_info.get("first_name")
        if user_info.get("last_name") and not user.last_name:
            update_data["last_name"] = user_info.get("last_name")
            
        # Apply updates if any
        if update_data:
            user = await update_user(db, user_id=user.id, update_data=update_data)
    else:
        # Create new user with OAuth info
        user_data = {
            "email": email,
            "first_name": user_info.get("first_name"),
            "last_name": user_info.get("last_name"),
            "avatar_url": user_info.get("avatar"),
            "oauth_provider": provider,
            "oauth_id": user_info.get("id")
        }
        user = await create_oauth_user(db, user_data)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": user.email, "user_id": user.id}
    
    # Store refresh token securely if provided
    if oauth_result["tokens"].get("refresh_token"):
        # In a production app, store the encrypted refresh token in the database
        refresh_token = oauth_result["tokens"].get("refresh_token")
        encrypted_token = encrypt_data(refresh_token)
        # TODO: Store encrypted_token in user.oauth_refresh_tokens[provider]
        logger.info(f"Received refresh token for {provider} OAuth")
    
    # Create app access token
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


async def refresh_oauth_tokens(db: AsyncSession, user: User, provider: str) -> Dict[str, Any]:
    """
    Refresh OAuth access tokens using the stored refresh token.
    
    Args:
        db: Database session
        user: User model
        provider: OAuth provider name
        
    Returns:
        Dict with new tokens
    """
    # This is a placeholder for the actual implementation
    # In a real app, you would:
    # 1. Retrieve the encrypted refresh token from the database
    # 2. Decrypt it
    # 3. Make a token refresh request to the provider
    # 4. Store the new refresh token (if provided)
    # 5. Return the new access token
    
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    # TODO: Implement actual token refresh logic with the provider
    
    return {
        "access_token": "refreshed_access_token",
        "token_type": "bearer",
        "expires_in": 3600
    }


def revoke_oauth_access(user: User, provider: str) -> bool:
    """
    Revoke OAuth access for a user.
    
    Args:
        user: User model
        provider: OAuth provider name
        
    Returns:
        Success status
    """
    # TODO: Implement actual token revocation with the provider
    # and clear the stored provider ID and refresh token
    
    return True 