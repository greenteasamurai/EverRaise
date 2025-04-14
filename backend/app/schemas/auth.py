from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class Token(BaseModel):
    """
    Token response schema.
    """
    access_token: str
    token_type: str
    user: UserResponse


class TokenPayload(BaseModel):
    """
    Token payload schema (JWT claims).
    """
    sub: Optional[str] = None
    exp: Optional[int] = None
    user_id: Optional[int] = None


class AuthResponse(Token):
    """
    Auth response including token and user data.
    """
    user: UserResponse


class GoogleOAuthRequest(BaseModel):
    """
    Request schema for Google OAuth authentication.
    """
    code: str
    redirect_uri: str


class MicrosoftOAuthRequest(BaseModel):
    """
    Request schema for Microsoft OAuth authentication.
    """
    code: str
    redirect_uri: str


class SlackOAuthRequest(BaseModel):
    """
    Request schema for Slack OAuth authentication.
    """
    code: str
    redirect_uri: str


class LoginRequest(BaseModel):
    """
    Login request schema.
    """
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """
    Register request schema.
    """
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class PasswordResetRequest(BaseModel):
    """
    Password reset request schema.
    """
    email: EmailStr


class PasswordChangeRequest(BaseModel):
    """
    Password change request schema.
    """
    current_password: str
    new_password: str


class OAuth2TokenExchangeRequest(BaseModel):
    """
    OAuth2 token exchange request schema.
    """
    provider: str = Field(..., description="OAuth provider (e.g., 'google', 'microsoft', 'slack')")
    code: str = Field(..., description="OAuth authorization code")
    redirect_uri: str = Field(..., description="Redirect URI used in the OAuth flow")