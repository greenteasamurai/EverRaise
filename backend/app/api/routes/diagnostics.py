from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import httpx
import asyncio
import time
import json
import os
from typing import Dict, Any

from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

@router.get("/ollama/status")
async def check_ollama_status():
    """Check if Ollama is running and available."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                models_list = [model.get("name") for model in models]
                return {
                    "available": True,
                    "url": settings.OLLAMA_BASE_URL,
                    "models": models_list,
                    "llama2_available": "llama2" in str(models_list).lower()
                }
            else:
                return {
                    "available": False,
                    "status_code": response.status_code,
                    "url": settings.OLLAMA_BASE_URL,
                    "error": f"Unexpected status: {response.status_code}"
                }
    except Exception as e:
        logger.error(f"Error checking Ollama status: {str(e)}")
        return {
            "available": False,
            "url": settings.OLLAMA_BASE_URL,
            "error": str(e)
        }

@router.post("/ollama/test")
async def test_ollama_generation():
    """Test Ollama generation with a simple prompt."""
    prompt = "Briefly explain why the sky is blue in one sentence."
    
    try:
        start_time = time.time()
        
        # Log the request we're about to make
        logger.info(f"Testing Ollama with model: {settings.OLLAMA_MODEL}, URL: {settings.OLLAMA_BASE_URL}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": prompt},
                timeout=30.0
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "duration_seconds": duration,
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "response": result,
                    "url": settings.OLLAMA_BASE_URL
                }
            else:
                return {
                    "success": False,
                    "duration_seconds": duration,
                    "status_code": response.status_code,
                    "error": f"Non-200 response: {response.text}",
                    "url": settings.OLLAMA_BASE_URL
                }
    except httpx.TimeoutException:
        duration = time.time() - start_time
        logger.error(f"Timeout after {duration:.2f}s when connecting to Ollama")
        return {
            "success": False,
            "duration_seconds": duration,
            "error": "Request timed out. Ollama may be taking too long to respond.",
            "url": settings.OLLAMA_BASE_URL
        }
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error testing Ollama generation: {str(e)}")
        return {
            "success": False,
            "duration_seconds": duration,
            "error": str(e),
            "url": settings.OLLAMA_BASE_URL
        }

@router.get("/env")
async def get_environment_config():
    """Get relevant environment configuration for diagnosis."""
    env_vars = {
        "OLLAMA_BASE_URL": settings.OLLAMA_BASE_URL,
        "OLLAMA_MODEL": settings.OLLAMA_MODEL,
        "LLM_TIMEOUT": settings.LLM_TIMEOUT,
        "LLM_MAX_TOKENS": settings.LLM_MAX_TOKENS,
        "ENVIRONMENT": settings.ENVIRONMENT
    }
    
    # Check if reports generation endpoint exists
    reports_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "routes", "reports.py")
    reports_exists = os.path.exists(reports_path)
    
    return {
        "environment_variables": env_vars,
        "diagnostics": {
            "reports_router_exists": reports_exists
        }
    } 