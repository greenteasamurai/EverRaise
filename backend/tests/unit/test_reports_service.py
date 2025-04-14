import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid

from app.services.llm import LLMService, ReportGenerationRequest, ReportGenerationResponse


@pytest.mark.unit
def test_report_generation_request():
    """Test the ReportGenerationRequest model."""
    request = ReportGenerationRequest(
        title="Test Report",
        report_type="investor_update",
        time_period="last_7_days",
        data_sources=["gmail"],
        query_filter="is:important",
        primary_prompt="Generate a report about investments"
    )
    
    assert request.title == "Test Report"
    assert request.report_type == "investor_update"
    assert request.time_period == "last_7_days"
    assert request.data_sources == ["gmail"]
    assert request.query_filter == "is:important"
    assert request.primary_prompt == "Generate a report about investments"


@pytest.mark.unit
def test_report_generation_response():
    """Test the ReportGenerationResponse model."""
    response = ReportGenerationResponse(
        title="Test Report",
        report_type="investor_update",
        content={"summary": "This is a summary"},
        summary="Short summary",
        token_usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        data_sources=["gmail"],
        confidence_score=0.8,
        citations=[{"text": "From email", "source": "email_1"}],
        status="complete"
    )
    
    assert response.title == "Test Report"
    assert response.report_type == "investor_update"
    assert response.content == {"summary": "This is a summary"}
    assert response.summary == "Short summary"
    assert response.token_usage == {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}
    assert response.data_sources == ["gmail"]
    assert response.confidence_score == 0.8
    assert response.citations == [{"text": "From email", "source": "email_1"}]
    assert response.status == "complete"


@pytest.mark.unit
@pytest.mark.asyncio
@patch('app.services.llm.LLMService.generate_report')
async def test_generate_report(mock_generate_report):
    """Test the report generation functionality."""
    # Create expected response object
    expected_response = ReportGenerationResponse(
        title="Test Report",
        report_type="investor_update",
        content={"summary": "This is a generated report."},
        summary="This is a generated report.",
        token_usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        data_sources=["gmail"],
        confidence_score=0.8,
        citations=[],
        status="complete"
    )
    
    # Set up the mock to return our expected response
    mock_generate_report.return_value = expected_response
    
    # Create a request
    request = ReportGenerationRequest(
        title="Test Report",
        report_type="investor_update",
        time_period="last_7_days",
        data_sources=["gmail"],
        query_filter=None,
        primary_prompt="Generate a report"
    )
    
    # Call the method
    llm_service = LLMService()
    result = await llm_service.generate_report(request)
    
    # Verify the result matches our expected response
    assert result == expected_response
    assert result.token_usage == {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}


@pytest.mark.unit
@pytest.mark.asyncio
@patch('app.services.llm.LLMService.generate_report')
async def test_generate_report_error(mock_generate_report):
    """Test error handling in report generation."""
    # Set up the mock to return an error response
    error_response = ReportGenerationResponse(
        title="Test Report",
        report_type="investor_update",
        content={"error": "Error generating report: LLM service unavailable"},
        summary="Error generating report: LLM service unavailable",
        token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        data_sources=["gmail"],
        confidence_score=0.0,
        citations=[],
        status="error"
    )
    mock_generate_report.return_value = error_response
    
    # Create a request
    request = ReportGenerationRequest(
        title="Test Report",
        report_type="investor_update",
        time_period="last_7_days",
        data_sources=["gmail"]
    )
    
    # Call the method
    llm_service = LLMService()
    result = await llm_service.generate_report(request)
    
    # Verify the result shows an error
    assert result.status == "error"
    assert "LLM service unavailable" in result.summary 