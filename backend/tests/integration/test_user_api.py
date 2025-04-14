import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
import uuid
from sqlalchemy import select

from app.core.security import get_password_hash
# Import actual User and Organization models
from app.db.models.user import User 
from app.db.models.organization import Organization

# Use fixtures defined in conftest
from tests.conftest import test_client, test_db, test_user, test_superuser, test_organization, user_auth_headers, superuser_auth_headers

# Constants
USERS_ENDPOINT = "/api/v1/users"

@pytest.mark.integration
class TestUserAPI:
    """
    Integration tests for the User API endpoints.
    
    These tests require a functioning database connection and test the full API stack.
    """
    
    @pytest.mark.asyncio
    # Inject test_organization fixture
    async def test_create_user(self, test_client: AsyncClient, test_db: AsyncSession, test_organization: Organization, superuser_auth_headers: dict):
        """Test creating a new user (requires superuser)."""
        unique_email = f"newuser_{uuid.uuid4()}@example.com"  # Generate unique email
        user_data = {
            "email": unique_email,
            "password": "newpassword123",
            "password_confirm": "newpassword123",
            "first_name": "New",
            "last_name": "User",
            "organization_id": test_organization.id # Include org ID
        }
        # Await needed here
        response = await test_client.post(USERS_ENDPOINT + "/", json=user_data, headers=superuser_auth_headers)
        assert response.status_code == 201, f"Failed to create user: {response.text}"
        created_user = response.json()
        assert created_user["email"] == unique_email
        assert "id" in created_user
        # Verify user exists in DB (optional)
        db_user = await test_db.get(User, created_user["id"])
        assert db_user is not None
        assert db_user.email == unique_email
    
    @pytest.mark.asyncio
    # Inject test_user fixture (which depends on test_organization) and user_auth_headers
    async def test_get_user(self, test_client: AsyncClient, test_user: User, user_auth_headers: dict):
        """Test retrieving a specific user (requires auth)."""
        # Retrieve the user created by the fixture
        # Await needed here
        response = await test_client.get(f"{USERS_ENDPOINT}/{test_user.id}", headers=user_auth_headers)
        assert response.status_code == 200, f"Failed to get user: {response.text}"
        user = response.json()
        assert user["id"] == test_user.id
        assert user["email"] == test_user.email
    
    @pytest.mark.asyncio
    # Inject test_superuser and superuser_auth_headers
    async def test_get_users(self, test_client: AsyncClient, test_db: AsyncSession, test_superuser: User, superuser_auth_headers: dict):
        """Test retrieving a list of users (requires superuser)."""
        # Ensure at least the test_user exists (created by fixture)
        # Await needed here
        response = await test_client.get(USERS_ENDPOINT + "/", headers=superuser_auth_headers)
        assert response.status_code == 200, f"Failed to get users list: {response.text}"
        users = response.json()
        assert isinstance(users, list)
        # Check if the fixture user is in the list
        found = any(u["id"] == test_superuser.id for u in users)
        assert found, "Fixture user not found in the list of users."
    
    @pytest.mark.asyncio
    # Inject test_user, test_organization, user_auth_headers
    async def test_update_user(self, test_client: AsyncClient, test_db: AsyncSession, test_user: User, user_auth_headers: dict):
        """Test updating a user's details (requires auth for self, or superuser for others)."""
        update_data = {"first_name": "UpdatedFirstName"}
        # Update own user details
        # Await needed here
        response = await test_client.put(f"{USERS_ENDPOINT}/{test_user.id}", json=update_data, headers=user_auth_headers)
        assert response.status_code == 200, f"Failed to update user: {response.text}"
        updated_user = response.json()
        assert updated_user["first_name"] == "UpdatedFirstName"
        assert updated_user["email"] == test_user.email # Email shouldn't change here

        # Verify update in DB
        await test_db.refresh(test_user)
        assert test_user.first_name == "UpdatedFirstName"
    
    @pytest.mark.asyncio
    # Inject test_db, test_organization, test_superuser, superuser_auth_headers
    async def test_delete_user(self, test_client: AsyncClient, test_db: AsyncSession, test_organization: Organization, test_superuser: User, superuser_auth_headers: dict):
        """Test deleting a user (requires superuser)."""
        # Create a user specifically for deletion in this test
        email_to_delete = f"delete_me_{uuid.uuid4()}@example.com"
        user_to_delete = User(
            email=email_to_delete,
            hashed_password=get_password_hash("deleteme"),
            first_name="Delete", last_name="Me", is_active=True
        )
        # Link to organization
        user_to_delete.organizations.append(test_organization)
        test_db.add(user_to_delete)
        # Explicitly commit the transaction to ensure the user is visible to the API
        await test_db.commit()
        # Refresh to get the ID
        await test_db.refresh(user_to_delete)
        user_id_to_delete = user_to_delete.id
        
        print(f"DEBUG: Created user with ID {user_id_to_delete} and email {email_to_delete} for deletion test")
        
        # Make sure the user exists before attempting to delete
        result = await test_db.execute(select(User).where(User.id == user_id_to_delete))
        verify_user = result.scalars().first()
        assert verify_user is not None, f"User with ID {user_id_to_delete} not found in database before deletion test"
        print(f"DEBUG: Verified user exists in database with ID {user_id_to_delete}")
        
        # Delete the user via API
        response = await test_client.delete(
            f"{USERS_ENDPOINT}/{user_id_to_delete}",
            headers=superuser_auth_headers
        )
        assert response.status_code == 200, f"Failed to delete user: {response.text}" # Assuming 200 OK on delete
        deleted_user_data = response.json()
        assert deleted_user_data["email"] == email_to_delete
        assert deleted_user_data["is_active"] is False  # Check soft deletion in response

        # Verify soft deletion in DB (is_active = False)
        await test_db.refresh(user_to_delete)
        assert user_to_delete is not None
        assert user_to_delete.is_active is False

    @pytest.mark.asyncio
    async def test_delete_user_not_found(
        self, test_client: AsyncClient, superuser_auth_headers: dict
    ):
        """Test deleting a non-existent user."""
        non_existent_id = 99997
        # Await needed here
        response = await test_client.delete(f"{USERS_ENDPOINT}/{non_existent_id}", headers=superuser_auth_headers)
        assert response.status_code == 404
        assert "User not found" in response.text 