from fastapi import APIRouter

from app.api.v1 import auth, users, reports, health, gmail, diagnostics, secure_data

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(gmail.router, prefix="/gmail", tags=["gmail"])
api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["diagnostics"])
api_router.include_router(secure_data.router, prefix="/secure", tags=["secure"]) 