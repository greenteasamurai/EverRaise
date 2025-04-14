import pytest
import pytest_asyncio
from sqlalchemy import text, MetaData, Table, Column, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import InvalidRequestError

TestBase = declarative_base()

# Simple test model that doesn't depend on other tables
class TestModel(TestBase):
    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_db_connection(test_db: AsyncSession):
    """Test basic database connection and transaction handling."""
    assert test_db.is_active
    try:
        # Use text() for raw SQL execution
        result = await test_db.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
    except Exception as e:
        pytest.fail(f"Database query failed within transaction: {e}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_db_connection_old(test_db: AsyncSession):
    """
    Test database connection using a simple query without depending
    on the application models.
    """
    # The test_db fixture already provides a transaction.
    # Do not begin a new one here.
    try:
        # Drop table first to ensure idempotency
        await test_db.execute(text("DROP TABLE IF EXISTS test_table"))
        await test_db.execute(text("CREATE TABLE test_table (id INTEGER PRIMARY KEY)"))
        # Test that we can execute a simple query
        result = await test_db.execute(text("SELECT 1"))
        assert result.scalar_one() == 1, "Database query failed"
    except Exception as e:
        pytest.fail(f"Test query failed: {e}") 