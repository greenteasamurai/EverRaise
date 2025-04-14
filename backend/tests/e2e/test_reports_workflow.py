import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
import time
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import Any, Dict
from httpx import AsyncClient
from sqlalchemy.future import select

from app.main import app
from app.api.deps import get_db
from app.core.config import settings
from app.db.models.user import User
from app.db.models.report import Report, ReportStatus
from app.db.models.organization import Organization
from app.schemas.report import ReportCreate

REPORTS_ENDPOINT = "/api/v1/reports"
GENERATE_ENDPOINT = f"{REPORTS_ENDPOINT}/generate"
NUM_REQUESTS = 10
CHECK_INTERVAL = 1  # seconds
MAX_WAIT_TIME = 60  # seconds

@pytest.mark.e2e
async def test_complete_report_generation_workflow(
    test_client: AsyncClient,
    test_db: AsyncSession,
    test_user: User,
    user_auth_headers: Dict[str, str]
):
    """E2E test for report generation: start, poll, check final status/data."""
    report_title = "E2E Test Report"
    report_type = "knowledge_summary"
    data_sources = ["gmail"]

    logger.info("Starting report generation...")

    # 1. Initiate report generation - Using the overridden client
    response = await test_client.post(
        GENERATE_ENDPOINT,
        headers=user_auth_headers,
        json={"title": report_title, "report_type": report_type, "data_sources": data_sources}
    )

    assert response.status_code == 202, f"Initial request failed: {response.text}"
    report_data = response.json()
    report_id = report_data.get("id")
    assert report_id is not None
    logger.info(f"Report generation initiated. Report ID: {report_id}")

    # 2. Poll for report status
    max_poll_time = 60  # seconds
    poll_interval = 2   # seconds
    start_time = time.time()
    final_status = None

    logger.info("Polling for report status...")
    while time.time() - start_time < max_poll_time:
        poll_response = await test_client.get(f"{REPORTS_ENDPOINT}/{report_id}", headers=user_auth_headers)
        if poll_response.status_code == 200:
            poll_data = poll_response.json()
            final_status = poll_data.get("status")
            logger.debug(f"Poll status: {final_status}")
            if final_status in ["completed", "failed"]:
                logger.info(f"Report reached terminal status: {final_status}")
                break
        else:
            logger.warning(f"Polling failed with status {poll_response.status_code}: {poll_response.text}")
            # Continue polling even if one poll fails, maybe transient issue

        await asyncio.sleep(poll_interval)
    else:
        # Timeout occurred
        pytest.fail(f"Polling timed out after {max_poll_time} seconds. Last status: {final_status}")

    # 3. Assert final status and optionally content
    assert final_status == "completed", f"Report did not complete successfully. Final status: {final_status}"

    # Optionally, retrieve the final report data and assert its contents
    final_report_response = await test_client.get(f"{REPORTS_ENDPOINT}/{report_id}", headers=user_auth_headers)
    assert final_report_response.status_code == 200
    final_report_data = final_report_response.json()

    assert final_report_data["title"] == report_title
    assert final_report_data["report_type"] == report_type
    # Example: Check if report_content exists and is not empty (adjust based on actual structure)
    assert "content" in final_report_data
    assert final_report_data["content"] is not None
    # Add more specific content assertions if needed
    logger.info(f"Report {report_id} completed successfully and verified.")


@pytest.mark.e2e
async def test_combine_reports_workflow(test_client: AsyncClient, user_auth_headers: dict):
    """Test the combine reports workflow (currently expects 501 Not Implemented)."""
    # Placeholder IDs - real implementation would generate reports first
    report_id_1 = 1 
    report_id_2 = 2

    combine_data = {
        "title": "Combined E2E Report",
        "report_ids": [report_id_1, report_id_2]
    }
    response_combine = await test_client.post("/api/v1/reports/combine", json=combine_data, headers=user_auth_headers)
    
    # Assert that the combine endpoint is correctly returning Not Implemented
    assert response_combine.status_code == 501, f"Combine endpoint returned unexpected status: {response_combine.status_code}"

async def poll_report_status(
    client: AsyncClient, 
    report_id: int, 
    headers: dict, 
    expected_status: ReportStatus,
    max_wait: int = MAX_WAIT_TIME
) -> Report:
    """Polls the report status until it reaches the expected status or times out."""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = await client.get(f"{REPORTS_ENDPOINT}/{report_id}", headers=headers)
        if response.status_code == 200:
            report_data = response.json()
            current_status = ReportStatus(report_data["status"])
            logger.debug(f"Polling Report ID {report_id}: Current status={current_status}")
            if current_status == expected_status:
                return Report(**report_data)
            if current_status == ReportStatus.FAILED:
                logger.error(f"Report {report_id} failed during generation: {report_data.get('error_message')}")
                raise AssertionError(f"Report {report_id} failed: {report_data.get('error_message')}")
        else:
            logger.warning(f"Polling Report ID {report_id}: Received status code {response.status_code}")
        await asyncio.sleep(CHECK_INTERVAL)
    raise TimeoutError(f"Report {report_id} did not reach status {expected_status.value} within {max_wait}s")

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_report_generation_workflow(
    test_client: AsyncClient, 
    test_db: AsyncSession, 
    user_auth_headers: dict
):
    """Tests the complete workflow: request, poll, and verify report generation."""
    request_data = {
        "title": "E2E Test Report",
        "report_type": "knowledge_summary",
        "data_sources": ["gmail"]
    }
    
    # 1. Request Report Generation
    initial_response = await test_client.post(f"{REPORTS_ENDPOINT}/generate", json=request_data, headers=user_auth_headers)
    assert initial_response.status_code == 202, f"Initial request failed: {initial_response.text}"
    report_initial = initial_response.json()
    report_id = report_initial["id"]
    assert report_initial["status"] == ReportStatus.PENDING.value
    logger.info(f"Report generation requested successfully. Report ID: {report_id}")

    # 2. Poll for Completion
    try:
        completed_report = await poll_report_status(test_client, report_id, user_auth_headers, ReportStatus.COMPLETED)
        assert completed_report.status == ReportStatus.COMPLETED
        assert completed_report.content is not None
        logger.info(f"Report {report_id} completed successfully.")

    except (TimeoutError, AssertionError) as e:
        pytest.fail(f"Polling or verification failed: {e}")

    # 3. Verify Report Content (Basic Check)
    final_response = await test_client.get(f"{REPORTS_ENDPOINT}/{report_id}", headers=user_auth_headers)
    assert final_response.status_code == 200
    final_report_data = final_response.json()
    assert final_report_data["status"] == ReportStatus.COMPLETED.value
    assert final_report_data["id"] == report_id
    assert "content" in final_report_data
    assert final_report_data["content"] is not None
    # Add more specific content validation if possible based on expected output
    logger.info(f"Final verification of Report {report_id} passed.")

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_combine_reports_workflow(
    test_client: AsyncClient, 
    test_db: AsyncSession, 
    user_auth_headers: dict
):
    """Tests combining multiple reports (requires pre-existing completed reports)."""
    # Create a couple of dummy reports for combination
    # Note: This uses direct DB interaction; adjust if using API-created reports
    user = await test_db.scalar(select(User).filter_by(email="testauth@example.com")) # Example user
    org = await test_db.scalar(select(Organization).filter_by(slug="auth-test-org")) # Example org
    
    if not user or not org:
        pytest.skip("Skipping combine test: dependent user or org not found.")

    # Create reports using direct database access
    # Note: The ReportCreate schema and create_report function need to be imported
    from app.schemas.report import ReportCreate
    from app.crud.report import create_report # Local import for clarity
    
    report1_data = ReportCreate(
        title="Combine Source 1", report_type="knowledge_summary", status=ReportStatus.COMPLETED,
        creator_id=user.id, organization_id=org.id,
        content=json.dumps({"key_findings": "Source 1 Findings"})
    )
    report2_data = ReportCreate(
        title="Combine Source 2", report_type="knowledge_summary", status=ReportStatus.COMPLETED,
        creator_id=user.id, organization_id=org.id,
        content=json.dumps({"key_findings": "Source 2 Findings"})
    )
    
    db_report1 = await create_report(test_db, report1_data)
    db_report2 = await create_report(test_db, report2_data)
    await test_db.commit() # Commit the source reports
    logger.info(f"Created source reports for combine test: ID {db_report1.id}, ID {db_report2.id}")

    # Request report combination
    combine_request = {
        "title": "Combined E2E Report",
        "report_ids": [db_report1.id, db_report2.id],
        "primary_prompt": "Combine the key findings."
    }
    combine_response = await test_client.post(f"{REPORTS_ENDPOINT}/combine", json=combine_request, headers=user_auth_headers)
    assert combine_response.status_code == 202, f"Combine request failed: {combine_response.text}"
    combined_report_initial = combine_response.json()
    combined_report_id = combined_report_initial["id"]
    assert combined_report_initial["status"] == ReportStatus.PENDING.value
    logger.info(f"Report combination requested. Combined Report ID: {combined_report_id}")

    # Poll for completion
    try:
        completed_combined_report = await poll_report_status(
            test_client, combined_report_id, user_auth_headers, ReportStatus.COMPLETED
        )
        assert completed_combined_report.status == ReportStatus.COMPLETED
        assert completed_combined_report.content is not None
        logger.info(f"Combined report {combined_report_id} completed successfully.")
        
        # Verify content includes elements from both sources (simple check)
        combined_content = json.loads(completed_combined_report.content)
        assert "Source 1 Findings" in combined_content.get("summary", "") or \
               "Source 1 Findings" in combined_content.get("combined_content", ""), \
               "Combined content doesn't seem to include Source 1"
        assert "Source 2 Findings" in combined_content.get("summary", "") or \
               "Source 2 Findings" in combined_content.get("combined_content", ""), \
               "Combined content doesn't seem to include Source 2"

    except (TimeoutError, AssertionError) as e:
        pytest.fail(f"Polling or verification of combined report failed: {e}") 