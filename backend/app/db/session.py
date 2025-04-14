import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Explicitly mark testing mode with an environment variable
# This is set by pytest fixtures
TESTING = os.environ.get("TESTING", "").lower() in ("true", "1", "t")

# Create different connection pool strategies for testing and production
if TESTING:
    # For testing use NullPool to ensure clean transactions between tests
    engine = create_async_engine(
        str(settings.DATABASE_URL), 
        echo=settings.DB_ECHO_LOG,
        poolclass=NullPool
    )
else:
    # For production/development use the default pool
    engine = create_async_engine(
        str(settings.DATABASE_URL), 
        echo=settings.DB_ECHO_LOG
    )

# Create session factory
async_session_factory = async_sessionmaker(
    bind=engine, 
    autocommit=False, 
    autoflush=False,
    expire_on_commit=False
)

# Global registry to track active sessions (helpful for debug)
_active_sessions = set()

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a new database session for each request.
    The session is closed when the request is done.
    """
    session = async_session_factory()
    _active_sessions.add(id(session))
    
    try:
        yield session
    finally:
        if session in _active_sessions:
            _active_sessions.remove(id(session))
            
        if not session.is_active:
            # Session already closed, nothing to do
            return
            
        try:
            await session.close()
        except Exception as e:
            # Log the exception but don't re-raise to ensure cleanup continues
            print(f"Error closing session: {e}")

async def create_db_and_tables() -> None:
    """
    Create database tables if they don't exist.
    This is called on application startup.
    """
    from app.db.base import Base
    
    async with engine.begin() as conn:
        # SQLAlchemy 2.0 syntax
        await conn.run_sync(Base.metadata.create_all)

# Create a synchronous engine (if needed for specific tools/tests)
sync_engine_url = str(settings.DATABASE_URL).replace('postgresql+asyncpg://', 'postgresql://')
sync_engine = create_engine(
    sync_engine_url,
    echo=False,
    pool_pre_ping=True
)

# Create synchronous session factory (if needed)
SessionLocal = sessionmaker(
    bind=sync_engine, autocommit=False, autoflush=False
) 