import time
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sentry_sdk
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.session import create_db_and_tables

# Configure Sentry for error monitoring (in production)
if settings.ENVIRONMENT != "development":
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
    )

# Configure logger
logger.add(
    "logs/everraise.log",
    rotation="500 MB",
    level="INFO",
    serialize=True,
    backtrace=True,
    diagnose=True,
)

app = FastAPI(
    title="EverRaise API",
    description="AI-powered business communication analytics platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Middleware for request timing and logging
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request details (avoid logging sensitive data)
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.4f}s"
        )
        return response

# Add middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

@app.get("/", tags=["Health"])
async def health_check():
    """
    Root endpoint for API health check.
    """
    return {"status": "healthy", "service": "EverRaise API", "version": "0.1.0"}

@app.get("/api", tags=["Health"])
async def api_health_check():
    """
    API root endpoint for frontend health check.
    This endpoint is used by the frontend to check if the backend is running.
    It doesn't require authentication.
    """
    return {"status": "online"}

@app.on_event("startup")
async def startup_event():
    """
    Initialize services on startup.
    """
    logger.info("Starting up EverRaise API...")
    # Create database tables
    await create_db_and_tables()
    logger.info("Database tables created")

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to log errors and provide consistent responses.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Our team has been notified."},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 