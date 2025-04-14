from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from loguru import logger
import uuid
import json
import asyncio
import httpx
from sqlalchemy import select

# RQ imports
from app.core.rq_config import queue # Import the configured RQ queue

from app.api.deps import get_db, get_current_user, get_current_user_optional
from app.db.models.user import User, Organization
from app.db.models.report import ReportStatus, ReportType
from app.services.llm import (
    LLMService, 
    ReportGenerationRequest,
    ReportGenerationResponse,
    ProgressUpdate
)
from app.schemas.report import ReportCreateRequest, ReportCreate, ReportUpdate, ReportRead, ReportList
from app.crud import report as crud_report
from app.db.session import async_session_factory # Import session factory for task

router = APIRouter()

# --- RQ Task Function ---
async def run_report_generation_task(report_id: int, llm_request_dict: dict):
    """RQ Task: Generates the report and updates the DB using its own session."""
    llm_service = LLMService()
    report_result: Optional[ReportGenerationResponse] = None
    report_update_data = {}
    start_time = asyncio.get_event_loop().time() # For generation_time
    final_status = ReportStatus.FAILED # Default to failed
    error_message = "Unknown error occurred in background task."

    # Reconstruct the LLM request from the dictionary
    # Ensure ReportGenerationRequest is properly reconstructable or adjust as needed
    try:
        llm_request = ReportGenerationRequest(**llm_request_dict)
    except Exception as pydantic_err:
        logger.error(f"[RQ Task ID:{report_id}] Failed to reconstruct ReportGenerationRequest: {pydantic_err}")
        error_message = f"Internal task setup error: {pydantic_err}"
        # Update status directly in the final block
        final_status = ReportStatus.FAILED
        report_update_data = {"status": final_status, "error_message": error_message}
        # Attempt to update DB even with setup error
        async with async_session_factory() as session:
            try:
                report_update_schema = ReportUpdate(**report_update_data)
                await crud_report.update_report(session, report_id, report_update_schema)
                await session.commit()
                logger.info(f"[RQ Task ID:{report_id}] Updated status to FAILED due to setup error.")
            except Exception as db_err:
                logger.error(f"[RQ Task ID:{report_id}] CRITICAL: Failed to update FAILED status after setup error: {db_err}")
        return # Stop processing if request cannot be reconstructed

    # --- Main Task Logic --- #
    try:
        logger.info(f"[RQ Task ID:{report_id}] Starting processing.")

        # --- Create session for this task run --- #
        async with async_session_factory() as session:
            logger.info(f"[RQ Task ID:{report_id}] Acquired DB session: {session}")

            # 1. Mark status as GENERATING
            generating_update = ReportUpdate(status=ReportStatus.GENERATING)
            await crud_report.update_report(session, report_id, generating_update)
            await session.commit() # Commit status change
            logger.info(f"[RQ Task ID:{report_id}] Marked status as GENERATING in DB.")

            # --- Run the LLM generation --- #
            # This part happens outside the session commit, but needs DB for final update

        # Run LLM Generation (can potentially take time)
        logger.info(f"[RQ Task ID:{report_id}] Calling LLM service...")
        report_result = await llm_service.generate_report(llm_request)
        end_time = asyncio.get_event_loop().time()
        generation_time = end_time - start_time
        logger.info(f"[RQ Task ID:{report_id}] LLM generation completed with status: {report_result.status} in {generation_time:.2f}s")

        # 3. Prepare final update data based on LLM result
        if report_result.status == "complete":
            final_status = ReportStatus.COMPLETED
            report_update_data = {
                "status": final_status,
                "content": json.dumps(report_result.content) if report_result.content else None,
                "meta_data": {
                    "summary": report_result.summary,
                    "citations": report_result.citations,
                    "data_sources_used": report_result.data_sources
                },
                "ai_model_used": report_result.token_usage.get("model", llm_service.default_model),
                "ai_confidence": report_result.confidence_score,
                "generation_time": generation_time,
                "token_count": report_result.token_usage.get("total_tokens"),
                "error_message": None # Clear any previous potential error
            }
        else:
            final_status = ReportStatus.FAILED
            error_message = f"LLM generation finished with status: {report_result.status}"
            report_update_data = {"status": final_status, "error_message": error_message, "generation_time": generation_time}

    except Exception as e:
        logger.error(f"[RQ Task ID:{report_id}] Error during report generation task: {e}", exc_info=True)
        final_status = ReportStatus.FAILED
        error_message = f"Internal error during report generation: {str(e)}"
        # Ensure generation_time is recorded if possible
        if 'end_time' not in locals(): end_time = asyncio.get_event_loop().time()
        generation_time = end_time - start_time
        report_update_data = {"status": final_status, "error_message": error_message, "generation_time": generation_time}

    # --- Final Update Attempt --- #
    finally:
        # Attempt to update the final status in the database using a new session
        async with async_session_factory() as final_session:
            try:
                # Ensure status is set, merge with existing data if any
                update_payload = {"status": final_status, "error_message": error_message, **report_update_data}
                report_update_schema = ReportUpdate(**update_payload)
                updated_report = await crud_report.update_report(final_session, report_id, report_update_schema)
                await final_session.commit()
                if updated_report:
                    logger.info(f"[RQ Task ID:{report_id}] Updated final report status in DB to: {updated_report.status}")
                else:
                    logger.error(f"[RQ Task ID:{report_id}] Failed to find report in DB for final update.")
            except Exception as db_err:
                logger.error(f"[RQ Task ID:{report_id}] CRITICAL: Failed to update report final status in DB: {db_err}", exc_info=True)

# --- API Endpoints --- #

@router.post("/generate", response_model=ReportRead, status_code=status.HTTP_202_ACCEPTED)
async def generate_report_endpoint(
    request: ReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),  # Use optional user dependency
):
    """
    Accept a report request, create DB entry, and enqueue generation task via RQ.
    Returns the initial report record with 'pending' status.
    """
    try:
        # Use test user for unauthenticated requests
        if not current_user:
            logger.info(f"Unauthenticated user requested report generation for '{request.title}' type '{request.report_type}'")
            # Get or create a default test user
            stmt = select(User).where(User.email == "testuser@example.com")
            result = await db.execute(stmt)
            test_user = result.scalars().first()
            
            if not test_user:
                # Create a test user if none exists
                from app.core.security import get_password_hash
                stmt = select(Organization).limit(1)
                result = await db.execute(stmt)
                org = result.scalars().first()
                
                if not org:
                    # Create a default organization if none exists
                    org = Organization(name="Test Organization", slug="test-org")
                    db.add(org)
                    await db.flush()
                
                test_user = User(
                    email="testuser@example.com",
                    hashed_password=get_password_hash("testpassword"),
                    first_name="Test",
                    last_name="User",
                    is_active=True
                )
                test_user.organizations.append(org)
                db.add(test_user)
                await db.flush()
                await db.refresh(test_user)
            
            current_user = test_user
        
        logger.info(f"User {current_user.email} (ID: {current_user.id}) requested report generation for '{request.title}' type '{request.report_type}'")

        # Validate ReportType enum
        try:
            report_type_enum = ReportType(request.report_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report_type: '{request.report_type}'. Valid types are: {[t.value for t in ReportType]}"
            )
            
        # Ensure user belongs to an organization (assuming primary organization for now)
        # Note: Accessing user.organizations might require relationship loading configuration
        # Depending on setup, you might need to query the organization separately
        # or ensure it's loaded when the user is fetched by get_current_user.
        # Let's assume it's loaded for now.
        if not current_user.organizations:
             logger.error(f"User {current_user.id} has no associated organization.")
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not associated with an organization.")
        current_org_id = current_user.organizations[0].id # Get the first associated org ID
        logger.info(f"Using Organization ID: {current_org_id} for user {current_user.id}")

        # Create internal schema for CRUD
        report_internal_create = ReportCreate(
            title=request.title,
            description=request.description,
            report_type=report_type_enum,
            organization_id=current_org_id,    # Use org ID from user
            creator_id=current_user.id,        # Use user ID from dependency
            status=ReportStatus.PENDING,
            meta_data={'initial_request': request.model_dump()} # Store initial request if helpful
        )
        
        # Create initial report record in DB
        db_report = await crud_report.create_report(db=db, report_in=report_internal_create)
        report_id = db_report.id # Get the integer ID
        logger.info(f"Created initial report record in DB with ID: {report_id}, Status: {db_report.status}")

        # Prepare request data for LLM service (ensure it's serializable)
        llm_report_request = ReportGenerationRequest(
            title=request.title,
            report_type=request.report_type, # String form
            time_period="not_specified",
            custom_start_date=None,
            custom_end_date=None,
            data_sources=request.data_sources or [],
            query_filter=None,
            sections=None,
            primary_prompt=None,
            secondary_prompts=None
        )
        llm_request_dict = llm_report_request.model_dump() # Convert to dict for RQ

        # --- Enqueue the task using RQ --- #
        job = queue.enqueue(
            run_report_generation_task, # The task function
            report_id,                # Arguments for the task function...
            llm_request_dict,
            job_timeout='10m'         # Set a reasonable timeout
            # result_ttl=86400       # How long to keep results (optional)
            # failure_ttl=604800     # How long to keep failed jobs (optional)
        )
        logger.info(f"Enqueued report generation task for DB ID {report_id}. RQ Job ID: {job.id}")

        # Update report with job ID (optional but useful for tracking)
        try:
            report_update_job_id = ReportUpdate(meta_data={'rq_job_id': job.id, **(db_report.meta_data or {})})
            await crud_report.update_report(db, report_id, report_update_job_id)
            await db.commit() # Commit the job ID update
            logger.info(f"Updated report {report_id} with RQ Job ID.")
        except Exception as e_job_update:
            logger.error(f"Failed to update report {report_id} with RQ Job ID {job.id}: {e_job_update}")
            # Don't fail the request, just log the error

        # Return the initial report record (status is PENDING)
        # Refresh db_report to get the updated metadata if needed, or just return original
        return db_report

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions directly
        raise http_exc
    except Exception as e:
        logger.error(f"Error initiating report generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start report generation process: {str(e)}",
        )

@router.get("/list", response_model=List[ReportList])
async def list_reports_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a list of reports (summary view).
    """
    logger.info(f"Retrieving report list (skip={skip}, limit={limit})")
    try:
        reports = await crud_report.list_reports(db, skip=skip, limit=limit)
        logger.info(f"Found {len(reports)} reports in DB.")
        # Response uses ReportList schema via response_model
        return reports
    except Exception as e:
        logger.error(f"Error retrieving report list: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report list."
        )

@router.get("/{report_id}", response_model=ReportRead)
async def get_report_endpoint(
    report_id: int, # Use integer ID
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific report by its ID.
    """
    logger.info(f"Retrieving report with ID: {report_id}")
    db_report = await crud_report.get_report(db, report_id=report_id)
    if db_report is None:
        logger.warning(f"Report ID {report_id} not found in database.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    logger.info(f"Successfully retrieved report {report_id} with status {db_report.status}")
    # Response uses ReportRead schema via response_model
    return db_report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report_endpoint(
    report_id: int, # Use integer ID
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a specific report by its ID.
    """
    logger.info(f"Attempting to delete report with ID: {report_id}")
    # Ensure report exists before attempting delete for clearer logging/errors
    db_report = await crud_report.get_report(db, report_id=report_id)
    if not db_report:
        logger.warning(f"Report ID {report_id} not found for deletion.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    deleted = await crud_report.delete_report(db, report_id=report_id)
    if not deleted:
        # This case should be rare if the get_report check passed
        logger.error(f"Report ID {report_id} found but failed to delete.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete report")

    logger.info(f"Successfully deleted report {report_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/types", response_model=List[Dict[str, Any]])
async def get_report_types(
):
    """
    Get available report types.
    """
    report_types = [
        {
            "id": "investor_update",
            "name": "Investor Update",
            "description": "Generate an investor update with key metrics, progress, and funding needs.",
            "default_sections": [
                "executive_summary", "key_metrics", "progress_update", "challenges", "funding_needs"
            ]
        },
        {
            "id": "business_review",
            "name": "Business Review",
            "description": "Generate a comprehensive business review including performance, market analysis, and strategic goals.",
            "default_sections": [
                "overview", "performance_analysis", "market_trends", "strategic_initiatives", "financial_summary"
            ]
        },
        {
            "id": "knowledge_summary",
            "name": "Knowledge Summary",
            "description": "Summarize key information from selected data sources based on a specific query.",
            "default_sections": [
                "query_summary", "key_findings", "relevant_excerpts", "action_items"
            ]
        },
        {
             "id": "meetings_tasks",
             "name": "Meetings & Tasks Summary",
             "description": "Summarize recent meetings, action items, and upcoming tasks.",
             "default_sections": [
                 "pending_tasks", "follow_up_items", "upcoming_deadlines", "scheduled_meetings", "completed_tasks", "notes_and_resources", "reminders"
             ]
        }
        # Add more report types as needed
    ]
    return report_types


@router.get("/data_sources", response_model=List[Dict[str, Any]])
async def get_data_sources(
):
    """
    Get available data sources for report generation.
    """
    data_sources = [
        {
            "id": "gmail",
            "name": "Gmail",
            "description": "Email messages from Gmail",
            "status": "available"
        },
        # Add other data sources as they become available
        {
            "id": "slack",
            "name": "Slack",
            "description": "Messages and channels from Slack",
            "status": "coming_soon"
        },
        {
            "id": "jira",
            "name": "Jira",
            "description": "Issues and epics from Jira",
            "status": "coming_soon"
        }
    ]
    
    return data_sources


class CombineReportsRequest(BaseModel):
    """API request model for combining reports."""
    title: str
    report_ids: List[int] # Should use int IDs now
    report_type: Optional[str] = None
    primary_prompt: Optional[str] = None


@router.post("/combine", response_model=Dict[str, Any])
async def combine_reports(
    request: CombineReportsRequest,
    db: AsyncSession = Depends(get_db),
):
    # !!! WARNING: This endpoint still relies on the old report_cache logic !!!
    # !!! It needs to be refactored to fetch reports from the database !!!
    logger.warning("The /combine endpoint is using outdated cache logic and needs refactoring.")
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Combine endpoint not yet updated for database persistence.")
    # ... (Keep old logic commented out or refactor later) ...


@router.get("/ollama-status", response_model=Dict[str, Any])
async def ollama_status():
    """
    Check the status of the Ollama LLM service.
    """
    result = {
        "available": False,
        "url": None,
        "models": [],
        "error": None,
        "response_time_ms": None,
        "simple_test": None
    }
    
    try:
        # Get Ollama URL from settings
        try:
            from app.core.config import settings
            ollama_url = settings.OLLAMA_BASE_URL
            result["url"] = ollama_url
        except Exception as e:
            result["error"] = f"Could not read OLLAMA_BASE_URL from settings: {str(e)}"
            return result
        
        import time
        import httpx
        
        # Check if Ollama is available
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to get the list of available models
                response = await client.get(f"{ollama_url}/api/tags")
                
                # Calculate response time
                end_time = time.time()
                result["response_time_ms"] = int((end_time - start_time) * 1000)
                
                if response.status_code == 200:
                    result["available"] = True
                    models_data = response.json()
                    
                    if "models" in models_data:
                        model_list = []
                        for model in models_data["models"]:
                            name = model.get("name", "unknown")
                            model_list.append(name)
                        result["models"] = model_list
                    else:
                        result["models"] = ["Unknown structure in response"]
                else:
                    result["error"] = f"Ollama returned status code: {response.status_code}"
        except Exception as e:
            end_time = time.time()
            result["response_time_ms"] = int((end_time - start_time) * 1000)
            result["error"] = f"Error connecting to Ollama: {str(e)}"
            return result
        
        # If Ollama is available, try a simple generation test
        if result["available"]:
            try:
                start_time = time.time()
                # Find the proper model to use
                model = settings.OLLAMA_MODEL
                if model not in result["models"]:
                    # If the configured model isn't available, use the first available model
                    model = result["models"][0] if result["models"] else "llama2"
                
                # Send a simple test prompt
                test_payload = {
                    "model": model,
                    "prompt": "Say hello in one word",
                    "stream": False
                }
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    test_response = await client.post(
                        f"{ollama_url}/api/generate", 
                        json=test_payload
                    )
                    
                    # Calculate test response time
                    end_time = time.time()
                    test_time_ms = int((end_time - start_time) * 1000)
                    
                    if test_response.status_code == 200:
                        result["simple_test"] = {
                            "success": True,
                            "model": model,
                            "response": test_response.json().get("response", "")[:50],
                            "time_ms": test_time_ms
                        }
                    else:
                        result["simple_test"] = {
                            "success": False,
                            "model": model,
                            "error": f"Status code: {test_response.status_code}",
                            "time_ms": test_time_ms
                        }
            except Exception as e:
                result["simple_test"] = {
                    "success": False,
                    "error": str(e)
                }
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
    
    return result