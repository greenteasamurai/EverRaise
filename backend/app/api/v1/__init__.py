from fastapi import APIRouter

from app.api.v1 import auth, gmail, reports, health, users
from app.api.routes import diagnostics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(gmail.router, prefix="/gmail", tags=["Gmail Integration"])
api_router.include_router(reports.router, prefix="/reports", tags=["Report Generation"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["Diagnostics"]) 