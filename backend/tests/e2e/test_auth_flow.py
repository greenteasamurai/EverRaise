import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from loguru import logger
from httpx import AsyncClient

from app.db.models.user import User
from app.core.security import get_password_hash
from tests.conftest import test_client, test_db, user_auth_headers
from app.core.config import settings
from app.db.models.organization import Organization
from app.schemas.user import UserCreate
from app.services.user import create_user, get_user_by_email
from app.core.security import verify_password


@pytest.mark.e2e
class TestAuthFlow:
    """
    End-to-end tests for the authentication flow.
    
    These tests verify the complete authentication process from registration to protected resource access.
    """
    
    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, test_client: TestClient, test_db: AsyncSession, test_user: User, user_auth_headers: dict):
        """Test the complete authentication flow from registration to resource access."""
        # Inject test_user fixture to get the actual user created for this test
        # Ensure the user from the token exists (created by fixtures)
        from app.services.user import get_user_by_email
        
        # Use the email from the injected test_user fixture
        user_from_db = await get_user_by_email(test_db, email=test_user.email)
        assert user_from_db is not None
        assert user_from_db.id == test_user.id

        # Access a protected endpoint with the fixture token
        me_response = await test_client.get(f"{settings.API_V1_STR}/auth/me", headers=user_auth_headers)
        assert me_response.status_code == 200, f"Protected endpoint access failed: {me_response.text}"
        
        # Verify the user data
        user_data = me_response.json()
        # Compare against the user object from the fixture
        assert user_data["email"] == test_user.email 
        assert user_data["first_name"] == test_user.first_name
        assert user_data["last_name"] == test_user.last_name
        
        # Test invalid credentials (using the test user's email)
        invalid_login_data = {
            "username": test_user.email, # Use 'username' for form data
            "password": "wrongpassword"
        }
        # Send as form data using `data=`
        invalid_response = await test_client.post(f"{settings.API_V1_STR}/auth/login", data=invalid_login_data)
        assert invalid_response.status_code == 401  # Unauthorized
        
        # Test invalid token format
        invalid_token_headers = {"Authorization": "Bearer invalidtoken12345"}
        invalid_token_response = await test_client.get(f"{settings.API_V1_STR}/auth/me", headers=invalid_token_headers)
        assert invalid_token_response.status_code == 401  # Unauthorized

    @pytest.mark.asyncio
    async def test_password_reset_flow(self, test_client: AsyncClient, test_db: AsyncSession):
        """Test the password reset flow."""
        email_for_reset = "resetuser_e2e@example.com"
        initial_password = "initialpassword_e2e"
        hashed_password = get_password_hash(initial_password)

        from app.db.models.organization import Organization
        
        # 1. Ensure Org Exists
        stmt = select(Organization).filter(Organization.name == "Reset Org E2E") # More specific query
        result = await test_db.execute(stmt)
        org = result.scalars().first()
        if not org:
            org = Organization(
                name="Reset Org E2E",
                slug=f"reset-org-e2e-{uuid.uuid4()}" # Add unique slug
            )
            test_db.add(org)
            await test_db.flush() # Get ID if new
            await test_db.refresh(org)

        # 2. Create User linked to Org
        reset_user = User(
            email=email_for_reset,
            hashed_password=hashed_password,
            first_name="ResetE2E",
            last_name="UserE2E",
            is_active=True
        )
        # reset_user.organization_id = org.id # Incorrect direct assignment
        test_db.add(reset_user)
        reset_user.organizations.append(org) # Correctly append to relationship list
        await test_db.flush() # Flush user and association
        await test_db.refresh(reset_user)
        user_id = reset_user.id # Store ID before potential rollback issues
        
        # 3. Request Password Reset (API Call)
        reset_request = {"email": email_for_reset}
        reset_response = await test_client.post("/api/auth/password-reset-request", json=reset_request)
        assert reset_response.status_code == 200, f"Password reset request failed: {reset_response.text}"
        
        # 4. Simulate Password Update (DB Interaction)
        reset_token = "mocked_reset_token_e2e" 
        new_password = "newSecurePassword_e2e"
        reset_user_from_db = await test_db.get(User, user_id) # Get user by stored ID
        assert reset_user_from_db is not None
        reset_user_from_db.hashed_password = get_password_hash(new_password)
        await test_db.flush() # Flush the password change
        
        # 5. Attempt Login with New Password (API Call - use data=)
        login_data_form = {"username": email_for_reset, "password": new_password}
        login_response = await test_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data_form)
        assert login_response.status_code == 200, f"Login with new password failed: {login_response.text}"
        login_resp_data = login_response.json()
        assert "access_token" in login_resp_data

        # 6. Attempt Login with Old Password (API Call - use data=)
        old_login_data_form = {"username": email_for_reset, "password": initial_password}
        old_login_response = await test_client.post(f"{settings.API_V1_STR}/auth/login", data=old_login_data_form)
        assert old_login_response.status_code == 401, f"Login with old password should fail, but got {old_login_response.status_code}: {old_login_response.text}"

    @pytest.mark.asyncio
    async def test_complete_auth_flow_explicit_commit(self, test_client: AsyncClient, test_db: AsyncSession):
        """Test registration, login, and accessing a protected endpoint.
        Includes an explicit commit after user creation to potentially resolve visibility issues.
        """
        logger.info("Starting complete auth flow test (with explicit commit)...")

        # 1. Ensure Organization Exists (or create)
        org = await test_db.scalar(select(Organization).filter_by(slug="auth-test-org"))
        if not org:
            org = Organization(name="Auth Test Org", slug="auth-test-org")
            test_db.add(org)
            await test_db.flush() # Flush to get org ID
            await test_db.refresh(org)
            logger.info(f"Created organization: {org.name} (ID: {org.id})")
        else:
            logger.info(f"Found existing organization: {org.name} (ID: {org.id})")

        # 2. Register New User
        logger.info(f"Attempting to register user: testauth@example.com")
        user_data = {
            "email": "testauth@example.com",
            "password": "testauthpassword",
            "password_confirm": "testauthpassword",
            "first_name": "Auth",
            "last_name": "User",
            "organization_id": org.id
        }
        response_register = await test_client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
        
        # Check registration success
        assert response_register.status_code == 200, f"Registration failed: {response_register.text}"
        register_data = response_register.json()
        assert "access_token" in register_data
        assert register_data["user"]["email"] == "testauth@example.com"
        logger.info(f"User testauth@example.com registered successfully.")

        # *** Explicitly commit the transaction after user creation via registration ***
        # This might be needed if the API's session management causes visibility issues for subsequent requests
        try:
            await test_db.commit()
            logger.info("Committed transaction after user registration.")
        except Exception as e:
            logger.error(f"Error committing transaction after registration: {e}")
            await test_db.rollback()
            raise # Re-raise the exception to fail the test if commit fails
        
        # Verify user exists in DB directly (using the test session)
        db_user = await test_db.scalar(select(User).filter_by(email="testauth@example.com"))
        assert db_user is not None, "User not found in DB after registration and commit."
        logger.info(f"Confirmed user testauth@example.com (ID: {db_user.id}) exists in DB via test session.")

        # 3. Login with the New User (use data=)
        login_payload_form = {"username": "testauth@example.com", "password": "testauthpassword"}
        logger.info(f"Attempting to login user: testauth@example.com")
        response_login = await test_client.post(f"{settings.API_V1_STR}/auth/login", data=login_payload_form)
        
        # Check login success
        assert response_login.status_code == 200, f"Login failed: {response_login.text}"
        login_data_resp = response_login.json()
        assert "access_token" in login_data_resp
        access_token = login_data_resp["access_token"]
        logger.info(f"User testauth@example.com logged in successfully.")

        # 4. Access Protected Endpoint (/me)
        headers = {"Authorization": f"Bearer {access_token}"}
        logger.info("Attempting to access /me endpoint...")
        response_me = await test_client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
        
        # Check /me endpoint access
        assert response_me.status_code == 200, f"Protected endpoint access failed: {response_me.text}"
        me_data = response_me.json()
        assert me_data["email"] == "testauth@example.com"
        logger.info("Successfully accessed /me endpoint.")
        logger.info("Complete auth flow test (with explicit commit) finished successfully.") 