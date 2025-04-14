import asyncio
import os
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator, Generator, Dict, Any
from sqlalchemy import create_engine, event, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from jose import jwt
from datetime import datetime, timedelta
import uuid
import logging
from loguru import logger
from httpx import AsyncClient
import httpx
from fastapi import FastAPI
from pytest_fastapi_deps import DependencyOverrider

from app.main import app
from app.api.deps import get_db  # Add import for get_db
from app.core.config import settings
# Correct import for get_async_session from session.py
from app.db.session import get_async_session, async_session_factory, engine
# Correct import for Base from base_class.py
from app.db.base_class import Base 
from app.core.security import create_access_token, get_password_hash

# Import the actual User and Organization models
from app.db.models.user import User
from app.db.models.organization import Organization
from app.db.models.report import Report, ReportTemplate, ReportSection, ReportVersion, report_data_source
# Import other models if they exist and are needed for table creation
# from app.db.models.embedding import ...

# Import RQ Queue for patching/testing
from rq import Queue
from rq.local import LocalStack
from rq.worker import SimpleWorker
from rq.job import Job
# from rq.queue import SimpleQueue # Removed - Not found/needed for patch
from app.core import rq_config # Import the module where the queue is defined

# Test database configuration
# If TEST_POSTGRES is set to 1, use PostgreSQL test database
# Otherwise, use SQLite in-memory database
USE_TEST_POSTGRES = os.environ.get("TEST_POSTGRES", "0") == "1"

# SQLite URL for quick tests
SQLITE_TEST_URL = "sqlite+aiosqlite:///:memory:"

# PostgreSQL URL for more realistic tests
# Using a different database name for tests to avoid affecting the development database
POSTGRES_TEST_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}_test"

# Select the appropriate test database URL
TEST_DB_URL = POSTGRES_TEST_URL if USE_TEST_POSTGRES else SQLITE_TEST_URL

# Override the dependency to use a test database
# Convert Pydantic URL to string before using replace
DATABASE_URL_STR = str(settings.DATABASE_URL)
TEST_DATABASE_URL = DATABASE_URL_STR.replace(
    DATABASE_URL_STR.split("/")[-1], 
    f"test_{DATABASE_URL_STR.split('/')[-1]}"
)

# Create test database engine
test_async_engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_async_engine, class_=AsyncSession, expire_on_commit=False
)

# Sync engine for test setup
test_sync_engine = create_engine(
    TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://") if "postgresql" in TEST_DATABASE_URL else TEST_DATABASE_URL
)

# Set testing environment variable to ensure session.py knows we're in test mode
os.environ["TESTING"] = "True"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def init_test_db(event_loop: asyncio.AbstractEventLoop) -> AsyncGenerator[None, None]:
    """
    Create test database tables, yield, then drop them when done.
    
    This is a session-scoped fixture that creates all tables before any tests run
    and drops them after all tests are complete.
    """
    from app.db.base import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    logger.debug("[Fixture] Test database initialized with all tables")
    yield
    
    # Optional cleanup
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    # logger.debug("[Fixture] Test database tables dropped")

@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh db session for a test.
    
    Each test gets its own transaction which is rolled back at the end.
    This ensures tests are isolated from each other.
    """
    logger.debug("[Fixture] Setting up transactional test_db session...")
    
    # Create a new session for this test
    session = async_session_factory()
    
    # Start a nested transaction
    await session.begin_nested()
    logger.debug(f"[Fixture] Transaction begun for test_db session: {session}")
    
    try:
        # Use the session in your tests
        yield session
    finally:
        # Always roll back the transaction
        logger.debug(f"[Fixture] Rolling back test_db session: {session}")
        await session.rollback()
        
        # Close the session when done
        logger.debug(f"[Fixture] Closing test_db session: {session}")
        await session.close()
        logger.debug(f"[Fixture] test_db session cleanup completed: {session}")

@pytest.fixture(scope="function")
async def test_client(
    event_loop: asyncio.AbstractEventLoop,
    init_test_db,
    test_db: AsyncSession
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Create a test client with a dependency override for the database session.
    """
    logger.debug("[Fixture] Setting up TestClient with override.")

    # We need to ensure the session from our test is used in the API
    async def override_get_async_session():
        logger.debug(f"[Override] Yielding test_db session for API call: {test_db}")
        try:
            yield test_db
        finally:
            logger.debug(f"[Override] Finished using test_db session for API call")

    # Create the app override
    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_db] = override_get_async_session

    # Create a test client with the ASGI app
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        follow_redirects=True
    ) as client:
        logger.debug("[Fixture] TestClient created")
        yield client
        logger.debug("[Fixture] TestClient released")

    # Clear the override after the test
    app.dependency_overrides.clear()
    logger.debug("[Fixture] TestClient dependency overrides cleared")

@pytest.fixture
def api_key_headers():
    """
    Generate headers with a test API key.
    """
    return {"X-API-Key": "test_api_key"}

def generate_test_token(email: str, superuser: bool = False) -> str:
    """Generate a test token for a user."""
    # Include is_superuser claim if needed by dependencies
    return create_access_token(
        data={"sub": email, "is_superuser": superuser},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

@pytest.fixture(scope="function")
def superuser_auth_headers(test_superuser: User) -> Dict[str, str]:
    """Fixture to generate authentication headers for a superuser."""
    token = generate_test_token(test_superuser.email, superuser=True)
    headers = {"Authorization": f"Bearer {token}"}
    logger.debug(f"[Fixture] Generated auth headers for superuser: {test_superuser.email}")
    return headers

@pytest.fixture(scope="function")
def user_auth_headers(test_user: User) -> Dict[str, str]:
    """Fixture to generate authentication headers for a regular user."""
    token = generate_test_token(test_user.email, superuser=False)
    headers = {"Authorization": f"Bearer {token}"}
    logger.debug(f"[Fixture] Generated auth headers for user: {test_user.email}")
    return headers

# Make email fixtures function-scoped for uniqueness
@pytest.fixture(scope="function") 
def test_superuser_email() -> str:
    return f"admin_{uuid.uuid4()}@example.com"

@pytest.fixture(scope="function")
def test_user_email() -> str:
    return f"user_{uuid.uuid4()}@example.com"

@pytest_asyncio.fixture(scope="function")
async def test_organization(test_db: AsyncSession) -> Organization:
    """Fixture to create a test organization."""
    org_name = f"Test Organization {uuid.uuid4()}"
    org_slug = f"test-org-{uuid.uuid4()}"
    org = Organization(
        name=org_name,
        slug=org_slug,
        description="Org for testing",
        is_active=True,
        plan_tier="free"
    )
    test_db.add(org)
    await test_db.commit()  # Ensure it's committed to the DB
    await test_db.refresh(org)
    logger.debug(f"[Fixture] Created Test Organization: {org.id} - {org.name}")
    return org

@pytest_asyncio.fixture(scope="function")
async def test_superuser(test_db: AsyncSession, test_organization: Organization) -> User:
    """Fixture to create a superuser test user associated with test_organization."""
    superuser_email = f"admin_{uuid.uuid4()}@example.com"
    superuser = User(
        email=superuser_email,
        hashed_password=get_password_hash("adminpassword"),
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_superuser=True,
        notification_email=True,
        notification_slack=True
    )
    superuser.organizations.append(test_organization) # Associate user with organization
    test_db.add(superuser)
    await test_db.commit()  # Ensure it's committed to the DB
    await test_db.refresh(superuser)
    logger.debug(f"[Fixture] Created Test Superuser: {superuser.id} - {superuser.email}")
    return superuser

@pytest_asyncio.fixture(scope="function")
async def test_user(test_db: AsyncSession, test_organization: Organization) -> User:
    """Fixture to create a regular test user associated with test_organization."""
    user_email = f"user_{uuid.uuid4()}@example.com"
    user = User(
        email=user_email,
        hashed_password=get_password_hash("password"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_superuser=False,
        notification_email=True,
        notification_slack=True
    )
    user.organizations.append(test_organization) # Associate user with organization
    test_db.add(user)
    await test_db.commit()  # Ensure it's committed to the DB
    await test_db.refresh(user)
    logger.debug(f"[Fixture] Created Test User: {user.id} - {user.email}")
    return user

# Removed seed_test_data fixture as user creation now handles org association.
# The user fixtures implicitly depend on test_organization, ensuring order.

# Helper for running async requests in tests if needed elsewhere
async def run_async_request(client: TestClient, method: str, url: str, **kwargs) -> Any:
    """Helper function to run async requests using the TestClient."""
    loop = asyncio.get_event_loop()
    # Use run_in_executor for synchronous TestClient methods within async tests
    response = await loop.run_in_executor(None, getattr(client, method), url, **kwargs)
    return response 