import pytest
import asyncio
import time
from typing import Any, Dict
from loguru import logger
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.main import app # Import your FastAPI app instance
from tests.conftest import run_async_request # Import helper

REPORTS_ENDPOINT = "/api/v1/reports/generate"
NUM_REQUESTS = 10  # Number of concurrent requests

# Test functions test_reports_list_performance and 
# test_generate_report_performance have been removed as they were outdated.

@pytest.mark.performance
async def test_report_generation_concurrency(
    test_client: AsyncClient, # Changed from TestClient to AsyncClient
    test_db: AsyncSession,
    user_auth_headers: Dict[str, str]
):
    """Test concurrent report generation requests using the overridden test_client."""

    start_time = time.time()
    responses = []

    logger.info(f"Sending {NUM_REQUESTS} concurrent requests to {REPORTS_ENDPOINT}...")

    # Tasks are created using the already overridden test_client
    tasks = []
    for i in range(NUM_REQUESTS):
        request_data = {
            "title": f"Perf Test Report {i+1}",
            "report_type": "knowledge_summary",
            "data_sources": ["gmail"]
        }
        # Directly create tasks with AsyncClient which supports native async/await
        tasks.append(asyncio.create_task(
            test_client.post(REPORTS_ENDPOINT, json=request_data, headers=user_auth_headers)
        ))

    # Gather results
    responses = await asyncio.gather(*tasks)

    end_time = time.time()

    total_time = end_time - start_time
    successful_requests = sum(1 for r in responses if r and r.status_code == 202)

    print(f"\n--- Report Generation Concurrency Test ---")
    print(f"Sent {NUM_REQUESTS} concurrent requests.")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Successful requests (202 Accepted): {successful_requests}/{NUM_REQUESTS}")
    print(f"Average time per request start: {total_time / NUM_REQUESTS:.2f} seconds")

    # Assert that all requests were accepted
    assert successful_requests == NUM_REQUESTS, f"Expected {NUM_REQUESTS} successful requests, got {successful_requests}"

    logger.info(f"Concurrency test completed in {total_time:.2f}s with {successful_requests} successful requests.")

async def run_async_request(client: AsyncClient, method: str, url: str, **kwargs):
    """Helper to run client requests in async context for asyncio.gather."""
    try:
        # Directly use AsyncClient which supports native async/await
        func = getattr(client, method)
        response = await func(url, **kwargs)
        return response
    except Exception as e:
        logger.error(f"Request failed during run_async_request: {e}")
        return None 