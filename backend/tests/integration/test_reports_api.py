import pytest
import pytest_asyncio
import asyncio
import json
from typing import Generator, AsyncGenerator
from unittest.mock import patch, AsyncMock, MagicMock
from loguru import logger # Import logger

from fastapi import status, Depends
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from httpx import AsyncClient # Use AsyncClient

# Import app and fixtures
from app.main import app
from app.db.models.user import User
from app.db.models.organization import Organization
# Correcting the import - we don't need to import the endpoint function
# from app.api.v1.reports import generate_report_endpoint

# Import models, schemas, and CRUD
from app.db.models.report import Report, ReportStatus, ReportType
from app.schemas.report import ReportRead, ReportList, ReportCreateRequest, ReportCreate, ReportUpdate
from app.services.llm import ReportGenerationResponse # For mocking LLM response
from app.crud import report as crud_report
from app.crud.report import create_report # Import create_report

# Define the base URL for reports API
REPORTS_API_URL = "/api/v1/reports"

# Use pytest marks for async tests
pytestmark = pytest.mark.asyncio

# --- Test Setup --- 
@pytest_asyncio.fixture(autouse=True)
async def setup_report_dependencies(test_user: User, test_organization: Organization):
    """Apply dependency overrides for report tests."""
    async def override_current_user_id() -> int:
        return test_user.id
    async def override_current_org_id() -> int:
        return test_organization.id
    
    # NOTE: This override section is currently commented out as the underlying endpoint
    # needs refactoring to use Depends(get_current_user) etc. instead of placeholders.
    # The test might still fail due to missing IDs until the endpoint is refactored.
    # Example of how it *should* work after endpoint refactor:
    # from app.api.deps import get_current_active_user # Assuming this dependency exists
    # async def override_get_current_active_user() -> User:
    #     return test_user
    # app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    yield
    # Clean up overrides if any were applied
    # app.dependency_overrides = {}


@pytest_asyncio.fixture(autouse=True)
async def setup_test_data(test_db: AsyncSession, test_user, test_organization):
    """Ensure a user and org exist for tests that need them."""
    # Fixtures from conftest handle creation
    pass

async def wait_for_report_completion(client: TestClient, report_id: int, timeout: int = 30, interval: int = 1):
    """Helper function to poll the report status until it's completed or failed."""
    for _ in range(timeout // interval):
        response = client.get(f"/api/v1/reports/{report_id}")
        if response.status_code == 200:
            data = response.json()
            if data["status"] in [ReportStatus.COMPLETED.value, ReportStatus.FAILED.value]:
                return data
        elif response.status_code == 404:
             # Report might not be found immediately if creation is slow? Unlikely with test setup.
             pass
        await asyncio.sleep(interval)
    pytest.fail(f"Report {report_id} did not complete or fail within {timeout} seconds.")


# --- Test Cases ---

@pytest.mark.asyncio
async def test_generate_report_success(
    test_client: AsyncClient, 
    test_db: AsyncSession, 
    test_user: User, 
    user_auth_headers: dict
):
    """Test successful report generation request (status 202)."""
    # Mock Redis queue to avoid connection errors
    job_id = "mock-job-id-12345"
    mock_job = MagicMock()
    mock_job.id = job_id
    
    # Create a mock for the queue.enqueue method
    mock_queue = MagicMock()
    mock_queue.enqueue.return_value = mock_job
    
    # Use patch to replace the queue with our mock during the test
    with patch('app.api.v1.reports.queue', mock_queue):
        request_data = {
            "title": "Integration Test Report",
            "report_type": "business_review",
            "data_sources": ["gmail", "slack"] # Example sources
        }
        # Await needed here
        response = await test_client.post(
            f"{REPORTS_API_URL}/generate", 
            json=request_data, 
            headers=user_auth_headers
        )
        
        # Verify the response
        assert response.status_code == 202, f"POST failed: {response.text}"
        report = response.json()
        assert report["title"] == "Integration Test Report"
        assert report["status"] == ReportStatus.PENDING.value
        assert report["creator_id"] == test_user.id
        assert "id" in report
        
        # Verify that our mock was called
        mock_queue.enqueue.assert_called_once()
        
        # The arguments should include the function and report ID
        args, kwargs = mock_queue.enqueue.call_args
        assert len(args) >= 1, "Expected at least one argument"
        # The first argument should be the task function
        assert args[0].__name__ == "run_report_generation_task", "Expected first argument to be the task function"

@pytest.mark.asyncio
async def test_generate_report_invalid_type(
    test_client: AsyncClient, 
    user_auth_headers: dict
):
    """Test report generation with an invalid report_type."""
    request_data = {"title": "Invalid Type Report", "report_type": "invalid_report_type"}
    # Await needed here
    response = await test_client.post(
        f"{REPORTS_API_URL}/generate", 
        json=request_data, 
        headers=user_auth_headers
    )
    assert response.status_code == 400 # Expect Bad Request
    assert "Invalid report_type" in response.text

@pytest.mark.asyncio
async def test_generate_report_llm_failure(
    test_client: AsyncClient, 
    test_db: AsyncSession, 
    test_user: User, 
    user_auth_headers: dict
):
    """Test report generation that simulates an LLM failure (mock needed)."""
    # This test requires mocking the LLMService or the underlying RQ task
    # to force a failure status update. Skipping actual implementation for now.
    pytest.skip("Skipping LLM failure test - requires mocking framework setup.")
    
    # Example structure if mocking was in place:
    # request_data = {"title": "LLM Fail Report", "report_type": "knowledge_summary"}
    # response = await test_client.post(f"{REPORTS_API_URL}/generate", json=request_data, headers=user_auth_headers)
    # assert response.status_code == 202
    # report_id = response.json()["id"]
    # 
    # # Wait for RQ worker (mocked) to process and set status to FAILED
    # await asyncio.sleep(2) # Adjust sleep as needed for mock execution
    # 
    # poll_response = await test_client.get(f"{REPORTS_API_URL}/{report_id}", headers=user_auth_headers)
    # assert poll_response.status_code == 200
    # assert poll_response.json()["status"] == ReportStatus.FAILED.value
    # assert "LLM processing failed" in poll_response.json().get("error_message", "")


@pytest.mark.asyncio
async def test_get_report(
    test_client: AsyncClient, 
    test_db: AsyncSession, 
    test_user: User, 
    test_organization: Organization, 
    user_auth_headers: dict
):
    """Test retrieving a specific report."""
    report_in = ReportCreate(
        title="Get Me Report", 
        report_type=ReportType.INVESTOR_UPDATE, 
        status=ReportStatus.COMPLETED, 
        creator_id=test_user.id,
        organization_id=test_organization.id, # Link to org
        content=json.dumps({"detail": "Sample content"})
    )
    db_report = await create_report(db=test_db, report_in=report_in)
    await test_db.commit() # Commit the report
    
    # Await needed here
    response = await test_client.get(f"{REPORTS_API_URL}/{db_report.id}", headers=user_auth_headers)
    assert response.status_code == 200
    report = response.json()
    assert report["id"] == db_report.id
    assert report["title"] == "Get Me Report"
    assert report["status"] == ReportStatus.COMPLETED.value

@pytest.mark.asyncio
async def test_get_report_not_found(
    test_client: AsyncClient, 
    user_auth_headers: dict
):
    """Test retrieving a non-existent report."""
    non_existent_id = 99999
    # Await needed here
    response = await test_client.get(f"{REPORTS_API_URL}/{non_existent_id}", headers=user_auth_headers)
    assert response.status_code == 404
    assert "Report not found" in response.text

@pytest.mark.asyncio
async def test_list_reports(
    test_client: AsyncClient, 
    test_db: AsyncSession, 
    test_user: User, 
    test_organization: Organization, 
    user_auth_headers: dict
):
    """Test listing reports."""
    # Create a few reports
    report_in_1 = ReportCreate(title="List Report 1", report_type="knowledge_summary", creator_id=test_user.id, organization_id=test_organization.id)
    report_in_2 = ReportCreate(title="List Report 2", report_type="business_review", creator_id=test_user.id, organization_id=test_organization.id)
    await create_report(db=test_db, report_in=report_in_1)
    await create_report(db=test_db, report_in=report_in_2)
    await test_db.commit()

    # Await needed here
    response = await test_client.get(f"{REPORTS_API_URL}/list", headers=user_auth_headers)
    assert response.status_code == 200
    reports = response.json()
    assert isinstance(reports, list)
    # Check if at least the created reports are in the list (could be more from other tests)
    report_titles = {r["title"] for r in reports}
    assert "List Report 1" in report_titles
    assert "List Report 2" in report_titles

@pytest.mark.asyncio
async def test_delete_report(
    test_client: AsyncClient, 
    test_db: AsyncSession, 
    test_user: User, 
    test_organization: Organization, 
    user_auth_headers: dict
):
    """Test deleting a report."""
    report_in = ReportCreate(
        title="Delete Me Report", 
        report_type="knowledge_summary", 
        creator_id=test_user.id,
        organization_id=test_organization.id
    )
    db_report = await create_report(db=test_db, report_in=report_in)
    await test_db.commit()
    report_id_to_delete = db_report.id

    # Await needed here
    delete_response = await test_client.delete(f"{REPORTS_API_URL}/{report_id_to_delete}", headers=user_auth_headers)
    assert delete_response.status_code == 204 # No Content

    # Verify deletion by trying to get it
    # Await needed here
    get_response = await test_client.get(f"{REPORTS_API_URL}/{report_id_to_delete}", headers=user_auth_headers)
    assert get_response.status_code == 404 # Not Found

@pytest.mark.asyncio
async def test_delete_report_not_found(
    test_client: AsyncClient, 
    user_auth_headers: dict
):
    """Test deleting a non-existent report."""
    non_existent_id = 99998
    # Await needed here
    response = await test_client.delete(f"{REPORTS_API_URL}/{non_existent_id}", headers=user_auth_headers)
    assert response.status_code == 404 # Not Found
    assert "Report not found" in response.text

# TODO: Add tests for invalid input to POST /generate (e.g., bad report_type)
# TODO: Add tests for /combine endpoint once refactored
# TODO: Improve mocking of background task for more reliable async testing 