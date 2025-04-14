import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.db.models.user import User
from app.db.models.organization import Organization

# Use fixtures from conftest
from tests.conftest import test_db, test_organization, test_user

@pytest.mark.integration
class TestDBModels:
    """
    Tests for basic model creation and relationships using a live test database.
    """

    @pytest.mark.asyncio
    async def test_create_organization(self, test_db: AsyncSession):
        """Test creating an Organization instance directly."""
        org_name = "Test Org DB"
        org_slug = "test-org-db"
        organization = Organization(name=org_name, slug=org_slug)
        test_db.add(organization)
        try:
            await test_db.commit()
            await test_db.refresh(organization)
        except OperationalError as e:
            pytest.fail(f"OperationalError during commit: {e}. Is the 'organization' table missing?")
        except IntegrityError as e:
            pytest.fail(f"IntegrityError during commit: {e}. Is the slug '{org_slug}' already used?")
        except Exception as e:
            pytest.fail(f"Unexpected error during organization creation: {e}")

        assert organization.id is not None
        assert organization.name == org_name
        assert organization.slug == org_slug

        # Clean up (optional, as fixtures should handle rollback)
        # await test_db.delete(organization)
        # await test_db.commit()

    @pytest.mark.asyncio
    async def test_create_user(self, test_db: AsyncSession, test_organization: Organization):
        """Test creating a User instance directly, linked to an organization."""
        user_email = "db_test_user@example.com"
        user = User(
            email=user_email,
            hashed_password="fakepassword",
            first_name="DBTest",
            last_name="User",
            # Removed organization_id
        )
        test_db.add(user)
        # Append organization to the relationship list
        user.organizations.append(test_organization)
        try:
            # Commit now saves user and the association table entry
            await test_db.commit()
            await test_db.refresh(user)
        except OperationalError as e:
            pytest.fail(f"OperationalError during commit: {e}. Is the 'user' table missing?")
        except IntegrityError as e:
            # IntegrityError could still happen if org doesn't exist or other constraint fails
            pytest.fail(f"IntegrityError during commit: {e}. Check constraints.")
        except Exception as e:
            pytest.fail(f"Unexpected error during user creation: {e}")

        assert user.id is not None
        assert user.email == user_email
        # Verify relationship by reloading the user and checking the list
        await test_db.refresh(user, attribute_names=['organizations'])
        assert len(user.organizations) == 1
        assert user.organizations[0].id == test_organization.id
        # assert user.organization_id == test_organization.id # This check is no longer valid

    @pytest.mark.asyncio
    async def test_user_organization_relationship(self, test_db: AsyncSession, test_user: User, test_organization: Organization):
        """Test accessing the user's organization via the relationship."""
        # Assuming test_user fixture is linked to test_organization fixture
        # Need to refresh to load relationships if not already loaded
        try:
            await test_db.refresh(test_user, ["organizations"]) 
        except OperationalError as e:
             pytest.fail(f"OperationalError during relationship refresh: {e}. Tables missing?")
        except Exception as e:
             pytest.fail(f"Unexpected error refreshing user relationship: {e}")

        assert test_organization in test_user.organizations
        assert test_user.organizations[0].id == test_organization.id