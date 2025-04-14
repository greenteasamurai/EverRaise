"""
Script to create an admin user in the database.
Run this script to ensure there's a known admin user to log in with.
"""

import asyncio
import sys
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import settings first to avoid circular imports
from app.core.config import settings

# Try importing models with error handling
try:
    from app.db.models.user import User
    from app.db.models.organization import Organization
    from app.core.security import get_password_hash
except ImportError as e:
    logger.error(f"Error importing models: {e}")
    logger.error("This might be due to circular imports or missing models.")
    logger.info("Attempting to continue with direct database operations...")


async def create_admin_user_direct(engine) -> None:
    """
    Create an admin user directly using SQL commands to avoid model issues.
    This is a fallback method when the ORM approach fails.
    """
    try:
        # Create a raw connection
        async with engine.begin() as conn:
            # Check if organization table exists
            try:
                # Check if admin org exists
                result = await conn.execute(
                    text("SELECT id FROM organization WHERE slug = 'admin-org' LIMIT 1")
                )
                org_id = result.scalar()
                
                if not org_id:
                    # Create organization
                    logger.info("Creating default organization...")
                    result = await conn.execute(
                        text("""
                        INSERT INTO organization (name, slug, description, is_active, plan_tier, created_at, updated_at)
                        VALUES ('Admin Organization', 'admin-org', 'Default organization for admin users', 1, 'premium', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        RETURNING id
                        """)
                    )
                    org_id = result.scalar()
                    logger.info(f"Created organization with ID: {org_id}")
                else:
                    logger.info(f"Using existing organization with ID: {org_id}")
                
                # Check if admin user exists
                result = await conn.execute(
                    text("SELECT id FROM user WHERE email = 'admin@example.com' LIMIT 1")
                )
                user_id = result.scalar()
                
                if not user_id:
                    # Import here to avoid circular imports
                    from app.core.security import get_password_hash
                    # Create admin user
                    hashed_password = get_password_hash("adminpassword")
                    logger.info("Creating admin user...")
                    result = await conn.execute(
                        text("""
                        INSERT INTO user (email, hashed_password, first_name, last_name, is_active, is_superuser, created_at, updated_at)
                        VALUES ('admin@example.com', :password, 'Admin', 'User', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        RETURNING id
                        """),
                        {"password": hashed_password}
                    )
                    user_id = result.scalar()
                    logger.info(f"Created admin user with ID: {user_id}")
                    
                    # Link user to organization
                    try:
                        await conn.execute(
                            text("""
                            INSERT INTO user_organization (user_id, organization_id, is_owner, created_at, updated_at)
                            VALUES (:user_id, :org_id, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """),
                            {"user_id": user_id, "org_id": org_id}
                        )
                        logger.info(f"Linked admin user to organization")
                    except Exception as e:
                        logger.error(f"Error linking user to organization: {e}")
                else:
                    logger.info(f"Admin user already exists with ID: {user_id}")
                    
            except Exception as e:
                logger.error(f"Error in database operations: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise


async def create_admin_user(db: AsyncSession) -> None:
    """Create an admin user if it doesn't exist yet using ORM."""
    try:
        # Check if admin already exists
        stmt = select(User).filter(User.email == "admin@example.com")
        result = await db.execute(stmt)
        admin = result.scalars().first()

        if admin:
            logger.info(f"Admin user already exists: {admin.email}")
            return admin

        # Check if any org exists
        stmt = select(Organization).limit(1)
        result = await db.execute(stmt)
        org = result.scalars().first()

        # Create a default organization if one doesn't exist
        if not org:
            logger.info("Creating default organization...")
            org = Organization(
                name="Admin Organization",
                slug="admin-org",
                description="Default organization for admin users",
                is_active=True,
                plan_tier="premium"
            )
            db.add(org)
            await db.flush()
            logger.info(f"Created organization: {org.name}")

        # Create admin user
        admin_user = User(
            email="admin@example.com",
            hashed_password=get_password_hash("adminpassword"),
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_superuser=True
        )
        
        # Associate admin with the organization
        admin_user.organizations.append(org)
        
        # Add to database
        db.add(admin_user)
        await db.commit()
        logger.info(f"Created admin user: {admin_user.email}")
        return admin_user
        
    except Exception as e:
        logger.error(f"Error in ORM admin creation: {e}")
        raise


async def main() -> None:
    """Main function to create admin user."""
    logger.info("Creating admin user...")
    
    # Setup DB connection
    engine = create_async_engine(str(settings.DATABASE_URL))
    
    try:
        # First try the ORM approach
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            try:
                await create_admin_user(session)
                logger.info("Admin user created successfully via ORM")
                return
            except Exception as e:
                logger.error(f"ORM approach failed: {e}")
                logger.info("Falling back to direct SQL approach...")
    
        # Fallback to direct SQL if ORM fails
        await create_admin_user_direct(engine)
        logger.info("Admin user created successfully via direct SQL")
        
    except Exception as e:
        logger.error(f"All admin creation approaches failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()
    
    logger.info("Done!")


if __name__ == "__main__":
    logger.info("Starting admin user creation script...")
    asyncio.run(main()) 