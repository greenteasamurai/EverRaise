from typing import Generator, Optional
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from loguru import logger

from app.core.config import settings
from app.db.session import SessionLocal, get_async_session
from app.db.models.user import User
from app.schemas.auth import TokenPayload

# OAuth2 compatible token scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
)

# Add an optional OAuth2 scheme that doesn't require authentication
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False  # Don't raise an exception if token is missing
)

# Dependency to get a database session
async def get_db() -> AsyncSession:
    """
    Get a database session as a dependency.
    """
    return await anext(get_async_session())

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Get the current authenticated user, eagerly loading the organizations relationship.
    Includes validation for token expiration and more detailed error handling.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Prepare a detailed error for authentication failures
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # First, try to decode the token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        # Validate the token structure
        token_data = TokenPayload(**payload)
        
        # Check for token expiration
        if not token_data.exp:
            logger.warning(f"Token missing expiration claim from {client_ip} ({user_agent})")
            raise credentials_exception
            
        expiration_datetime = datetime.fromtimestamp(token_data.exp)
        
        # Check if token is expired
        if expiration_datetime < datetime.now():
            logger.warning(f"Token expired for {token_data.sub} from {client_ip} ({user_agent})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Check if token is about to expire (within 5 minutes)
        if expiration_datetime < datetime.now() + timedelta(minutes=5):
            logger.info(f"Token for {token_data.sub} is about to expire soon")
            
        # Get subject (usually email) from token
        if not token_data.sub:
            logger.warning(f"Token missing subject claim from {client_ip} ({user_agent})")
            raise credentials_exception
            
        email = token_data.sub
        
    except ExpiredSignatureError:
        logger.warning(f"Explicitly expired token from {client_ip} ({user_agent})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (JWTError, ValidationError) as e:
        logger.warning(f"Invalid token from {client_ip} ({user_agent}): {str(e)}")
        raise credentials_exception
    
    # Get the user from the database, loading organizations
    stmt = select(User).options(selectinload(User.organizations)).where(User.email == email)
    
    try:
        result = await db.execute(stmt)
        user = result.scalars().first()
    except Exception as e:
        logger.error(f"Database error while validating user {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error during authentication",
        )
    
    if not user:
        logger.warning(f"User not found for email: {email} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User associated with token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Inactive user {email} tried to access from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Account is inactive. Please contact support.",
        )
    
    # Log successful authentication for audit purposes
    logger.info(f"Authenticated user {email} from {client_ip} ({user_agent})")
    
    return user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user with superuser permissions.
    """
    if not current_user.is_superuser:
        logger.warning(f"User {current_user.email} attempted to access superuser-only endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user

async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme_optional),
) -> Optional[User]:
    """
    Similar to get_current_user but returns None instead of raising an exception
    if the token is missing or invalid.
    """
    if not token:
        return None
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
        
    try:
        # Decode and validate the token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        # Check if token is expired
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            logger.warning(f"Expired token in optional auth from {client_ip} ({user_agent})")
            return None
            
        email = token_data.sub
        
    except (JWTError, ValidationError, KeyError) as e:
        logger.warning(f"Invalid token in optional auth from {client_ip}: {str(e)}")
        return None
    
    # Get the user from the database
    try:
        stmt = select(User).options(selectinload(User.organizations)).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalars().first()
    except Exception as e:
        logger.error(f"Database error in optional auth for {email}: {str(e)}")
        return None
    
    if not user:
        logger.warning(f"User not found in optional auth for email: {email}")
        return None
    
    if not user.is_active:
        logger.warning(f"Inactive user in optional auth: {email}")
        return None
    
    return user 