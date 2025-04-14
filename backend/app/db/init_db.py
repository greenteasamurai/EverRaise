"""
Database initialization script.
This script creates all tables and initializes the database.
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import engine, get_async_session
from app.db.base import Base
from app.core.config import settings

logger = logging.getLogger(__name__)

async def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    try:
        # Create tables
        async with engine.begin() as conn:
            logger.info("Creating database tables")
            # Drop all tables if in development mode and requested
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        
        # Verify database connection
        async for session in get_async_session():
            try:
                # Fixed: Use text() to properly format SQL query
                await session.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                break
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                raise
            finally:
                await session.close()
                
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

async def main():
    """Main function to run when script is executed directly"""
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Creating database at {settings.DATABASE_URL}")
    success = await init_db()
    if success:
        logger.info("Database initialization completed successfully")
    else:
        logger.error("Database initialization failed")

if __name__ == "__main__":
    asyncio.run(main()) 