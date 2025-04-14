from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import httpx
import asyncio
import os
import json
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.api.deps import get_current_active_user, get_db
from app.db.models.user import User
from app.services.gmail import GmailService
from app.services.llm import get_llm_status, test_simple_generation, LLMService, ReportGenerationRequest
from app.core.logging import logger

# Store the application start time for uptime calculation
APP_START_TIME = time.time()

router = APIRouter()

@router.get("/ollama/status", response_model=Dict[str, Any])
async def check_ollama_status():
    """
    Check the status of the Ollama LLM service
    """
    try:
        # Try to connect to the Ollama service
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            
            if response.status_code == 200:
                models_data = response.json().get("models", [])
                model_names = [model.get("name") for model in models_data]
                
                # Test if we can generate a simple response
                simple_test = await test_simple_generation()
                
                return {
                    "status": "connected",
                    "message": "LLM service is available",
                    "available": True,
                    "models": model_names,
                    "default_model": settings.OLLAMA_MODEL,
                    "default_model_available": settings.OLLAMA_MODEL in model_names,
                    "url": settings.OLLAMA_BASE_URL,
                    "simple_test": simple_test
                }
            else:
                return {
                    "status": "error",
                    "message": f"LLM service returned error: {response.status_code}",
                    "available": False,
                    "url": settings.OLLAMA_BASE_URL
                }
    except (httpx.ConnectError, httpx.ConnectTimeout, asyncio.TimeoutError):
        return {
            "status": "disconnected",
            "message": "Cannot connect to LLM service",
            "available": False,
            "url": settings.OLLAMA_BASE_URL
        }
    except Exception as e:
        logger.error(f"Error checking Ollama status: {str(e)}")
        return {
            "status": "error",
            "message": f"Error checking LLM status: {str(e)}",
            "available": False,
            "url": settings.OLLAMA_BASE_URL,
            "error": str(e)
        }

@router.get("/system/info")
async def system_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system diagnostic information (requires authentication)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access system diagnostics"
        )
    
    # Check database connectivity
    db_connected = False
    db_error = None
    try:
        # Execute a simple query to check database connectivity
        result = await db.execute(text("SELECT 1"))
        db_connected = result.scalar() == 1
    except Exception as e:
        db_error = str(e)
        logger.error(f"Database connectivity check failed: {e}")
    
    # Check Redis connection if configured
    redis_connected = False
    redis_error = None
    if settings.REDIS_URL:
        try:
            import redis.asyncio as redis
            r = redis.from_url(settings.REDIS_URL)
            await r.ping()
            redis_connected = True
            await r.close()
        except Exception as e:
            redis_error = str(e)
            logger.error(f"Redis connectivity check failed: {e}")
    
    # Get data directory stats
    data_dir_info = {}
    try:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        total_size = 0
        for root, dirs, files in os.walk(data_dir):
            if ".git" in root or "__pycache__" in root or "node_modules" in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        
        data_dir_info = {
            "path": data_dir,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "free_space_mb": round(
                os.statvfs(data_dir).f_frsize * os.statvfs(data_dir).f_bavail / (1024 * 1024), 2
            ) if hasattr(os, "statvfs") else "N/A"
        }
    except Exception as e:
        data_dir_info = {"error": str(e)}
    
    # Return enriched system diagnostics
    return {
        "database": {
            "type": settings.DATABASE_URL.split(":")[0] if settings.DATABASE_URL else "unknown",
            "connected": db_connected,
            "error": db_error
        },
        "redis": {
            "enabled": bool(settings.REDIS_URL),
            "connected": redis_connected,
            "url": settings.REDIS_URL.replace(settings.REDIS_PASSWORD, "****") if settings.REDIS_PASSWORD else settings.REDIS_URL,
            "error": redis_error
        },
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",  # Replace with actual version tracking
        "storage": data_dir_info,
        "server_time": datetime.now().isoformat(),
        "uptime_seconds": time.time() - APP_START_TIME
    }

@router.get("/database/status")
async def check_database_status(db: AsyncSession = Depends(get_db)):
    """
    Check the database connectivity and some basic stats
    """
    start_time = time.time()
    try:
        # Check database connectivity with a simple query
        result = await db.execute(text("SELECT 1 as is_alive"))
        is_alive = result.scalar() == 1
        
        # Get database stats if available
        stats = {}
        try:
            if settings.DATABASE_URL.startswith("sqlite"):
                # SQLite stats
                result = await db.execute(text("SELECT count(*) FROM sqlite_master WHERE type='table'"))
                table_count = result.scalar()
                stats["table_count"] = table_count
                
                # Get table sizes and row counts for main tables
                tables_info = []
                result = await db.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ))
                tables = [row[0] for row in result.fetchall()]
                
                for table in tables:
                    result = await db.execute(text(f"SELECT count(*) FROM '{table}'"))
                    row_count = result.scalar()
                    tables_info.append({"name": table, "row_count": row_count})
                
                stats["tables"] = tables_info
                
            elif settings.DATABASE_URL.startswith("postgresql"):
                # PostgreSQL stats
                result = await db.execute(text(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
                ))
                table_count = result.scalar()
                stats["table_count"] = table_count
                
                # Get table sizes
                result = await db.execute(text("""
                    SELECT 
                        relname as table_name,
                        n_live_tup as row_count,
                        pg_size_pretty(pg_total_relation_size(quote_ident(relname))) as total_size
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                """))
                tables_info = [
                    {"name": row[0], "row_count": row[1], "size": row[2]} 
                    for row in result.fetchall()
                ]
                stats["tables"] = tables_info
        except Exception as e:
            stats["error"] = str(e)
        
        query_time_ms = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": "connected" if is_alive else "error",
            "connected": is_alive,
            "type": settings.DATABASE_URL.split(":")[0] if settings.DATABASE_URL else "unknown",
            "response_time_ms": query_time_ms,
            "stats": stats
        }
    except Exception as e:
        query_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"Database status check failed: {e}")
        return {
            "status": "error",
            "connected": False,
            "type": settings.DATABASE_URL.split(":")[0] if settings.DATABASE_URL else "unknown",
            "response_time_ms": query_time_ms,
            "error": str(e)
        }

@router.get("/gmail/status")
async def check_gmail_status():
    """
    Check the status of the Gmail API integration
    """
    gmail_service = GmailService()
    try:
        # Check if credentials file exists
        credentials_file = settings.GMAIL_API_CREDENTIALS_FILE
        token_file = settings.GMAIL_API_TOKEN_FILE
        
        credentials_exist = os.path.exists(credentials_file)
        token_exists = os.path.exists(token_file)
        
        if not credentials_exist:
            return {
                "status": "error",
                "connected": False,
                "message": f"Credentials file not found: {credentials_file}",
                "auth_required": True
            }
        
        if not token_exists:
            # Try to generate auth URL
            try:
                # This will raise an exception with the auth URL
                gmail_service.authenticate()
            except Exception as e:
                if "Authentication required" in str(e):
                    # Extract the auth URL
                    auth_url = str(e).split("Please visit: ")[1] if "Please visit: " in str(e) else None
                    return {
                        "status": "auth_required",
                        "connected": False,
                        "message": "Authentication required for Gmail API",
                        "auth_url": auth_url,
                        "auth_required": True
                    }
                else:
                    return {
                        "status": "error",
                        "connected": False,
                        "message": f"Error during authentication: {str(e)}",
                        "auth_required": True
                    }
        
        # Try to authenticate and check if the service is available
        service = gmail_service.authenticate()
        
        # If we get here, authentication succeeded
        return {
            "status": "connected",
            "connected": True,
            "message": "Gmail API is available and authenticated",
            "auth_required": False
        }
    except Exception as e:
        logger.error(f"Gmail status check failed: {e}")
        return {
            "status": "error",
            "connected": False,
            "message": f"Error checking Gmail API: {str(e)}",
            "error": str(e),
            "auth_required": "Authentication required" in str(e)
        }

@router.get("/integrations")
async def check_all_integrations(
    db: AsyncSession = Depends(get_db)
):
    """
    Check the status of all integrations at once
    """
    results = {}
    
    # Check database
    try:
        db_status = await check_database_status(db)
        results["database"] = {
            "status": db_status["status"],
            "connected": db_status["connected"]
        }
    except Exception as e:
        results["database"] = {
            "status": "error",
            "connected": False,
            "error": str(e)
        }
    
    # Check Ollama
    try:
        ollama_status = await check_ollama_status()
        results["ollama"] = {
            "status": ollama_status["status"],
            "connected": ollama_status["status"] == "connected",
            "available": ollama_status.get("available", False)
        }
    except Exception as e:
        results["ollama"] = {
            "status": "error",
            "connected": False,
            "error": str(e)
        }
    
    # Check Gmail
    try:
        gmail_status = await check_gmail_status()
        results["gmail"] = {
            "status": gmail_status["status"],
            "connected": gmail_status["connected"],
            "auth_required": gmail_status.get("auth_required", False)
        }
    except Exception as e:
        results["gmail"] = {
            "status": "error",
            "connected": False,
            "error": str(e)
        }
    
    # Check Redis if enabled
    if settings.REDIS_URL:
        try:
            import redis.asyncio as redis
            r = redis.from_url(settings.REDIS_URL)
            await r.ping()
            results["redis"] = {
                "status": "connected",
                "connected": True
            }
            await r.close()
        except Exception as e:
            results["redis"] = {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
    else:
        results["redis"] = {
            "status": "disabled",
            "connected": False
        }
    
    # Overall status
    critical_services = ["database", "ollama"]
    all_critical_ok = all(results[service]["connected"] for service in critical_services)
    
    return {
        "status": "healthy" if all_critical_ok else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": results
    }

@router.get("/health")
async def health_check():
    """
    Basic health check endpoint that returns 200 if the service is up.
    This endpoint is public and can be used by load balancers or monitoring services.
    """
    try:
        # Check if Ollama is available
        ollama_status = False
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/version")
                ollama_status = response.status_code == 200
        except Exception:
            # Don't fail health check if Ollama is down
            pass
            
        # Check Redis if configured
        redis_status = False
        if settings.REDIS_URL:
            try:
                import redis.asyncio as redis
                r = redis.from_url(settings.REDIS_URL)
                redis_status = await r.ping()
                await r.close()
            except Exception:
                # Don't fail health check if Redis is down
                pass
                
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "dependencies": {
                "ollama": ollama_status,
                "redis": redis_status
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/report/test", response_model=Dict[str, Any])
async def test_report_generation():
    """
    Test the report generation capabilities with a simple prompt
    """
    try:
        # Create a minimal test request
        test_request = ReportGenerationRequest(
            title="Diagnostic Test Report",
            report_type="knowledge_summary",  # Simple report type
            time_period="last_7_days",
            data_sources=["test_data"],
            query_filter="diagnostic test",
        )
        
        start_time = time.time()
        
        # Initialize the LLM service
        llm_service = LLMService()
        
        # Test only the vector store creation
        test_data = [
            {"content": "This is a test document for diagnostics.", "metadata": {"source": "diagnostic_test"}}
        ]
        
        try:
            # Test vector store creation
            vector_store_start = time.time()
            vector_store = llm_service.create_vectorstore_from_texts(test_data)
            vector_store_time = time.time() - vector_store_start
            vector_store_success = True
        except Exception as vs_error:
            vector_store_success = False
            vector_store_time = time.time() - vector_store_start
            logger.error(f"Vector store creation error: {str(vs_error)}")
        
        # Try a simple generation
        try:
            generation_start = time.time()
            simple_result = await llm_service.generate_text(
                llm_service.LLMRequest(prompt="Generate a one sentence test response about business reports.")
            )
            generation_time = time.time() - generation_start
            generation_success = True
            generation_text = simple_result.text
        except Exception as gen_error:
            generation_success = False
            generation_time = time.time() - generation_start
            generation_text = None
            logger.error(f"Text generation error: {str(gen_error)}")
        
        # Get overall system status
        total_time = time.time() - start_time
        overall_status = "operational" if (vector_store_success and generation_success) else "degraded"
        
        if not vector_store_success and not generation_success:
            overall_status = "failing"
        
        return {
            "status": overall_status,
            "response_time_ms": round(total_time * 1000, 2),
            "vectorstore_test": {
                "success": vector_store_success,
                "time_ms": round(vector_store_time * 1000, 2),
                "document_count": len(test_data)
            },
            "generation_test": {
                "success": generation_success,
                "time_ms": round(generation_time * 1000, 2),
                "response": generation_text,
                "model": llm_service.default_model
            },
            "llm_connection": await get_llm_status(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Overall report diagnostic test failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/queue/status", response_model=Dict[str, Any])
async def check_queue_status():
    """
    Check the status of the Redis Queue (RQ) for report generation
    """
    try:
        from app.core.rq_config import redis_conn, queue
        
        # Check Redis connection
        redis_connected = False
        redis_error = None
        try:
            redis_ping = redis_conn.ping()
            redis_connected = redis_ping
        except Exception as e:
            redis_error = str(e)
            logger.error(f"Redis connection error: {str(e)}")
        
        # Get queue statistics
        queue_stats = {}
        if redis_connected:
            try:
                queue_stats = {
                    "name": queue.name,
                    "count": queue.count,
                    "failed_job_count": queue.failed_job_registry.count,
                    "scheduled_job_count": queue.scheduled_job_registry.count,
                    "job_ids": [job_id for job_id in queue.job_ids][:10],  # Show max 10 job IDs
                }
                
                # Show recent failed jobs
                failed_jobs = []
                for job_id in queue.failed_job_registry.get_job_ids()[:5]:  # Get at most 5 failed jobs
                    job = queue.fetch_job(job_id)
                    if job:
                        failed_jobs.append({
                            "id": job.id,
                            "created_at": job.created_at.isoformat() if job.created_at else None,
                            "exc_info": job.exc_info if hasattr(job, 'exc_info') else "Unknown error",
                        })
                
                queue_stats["recent_failed_jobs"] = failed_jobs
                
            except Exception as e:
                queue_stats = {"error": str(e)}
        
        return {
            "redis_connected": redis_connected,
            "redis_error": redis_error,
            "queue_stats": queue_stats,
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        return {
            "status": "error",
            "error": "RQ or Redis dependencies not available",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Queue status check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 