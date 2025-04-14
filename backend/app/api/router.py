from fastapi import APIRouter

from app.api.v1 import api_router as v1_router
from app.api.v1 import auth # Import the auth router

# Create main API router
api_router = APIRouter()

# Include API v1 router (which includes reports, users, etc.)
api_router.include_router(v1_router, prefix="/v1") 

# Include the authentication router directly under /api/auth
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"]) 