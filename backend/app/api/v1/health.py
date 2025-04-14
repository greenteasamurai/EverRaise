from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db

router = APIRouter()

@router.get("")
async def check_health(db: AsyncSession = Depends(get_db)):
    """
    Simple health check endpoint to verify API is running.
    Also checks database connection.
    """
    try:
        # Check database connection
        await db.execute("SELECT 1")
        
        return {
            "status": "ok",
            "message": "API is operational",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "API is running but database connection failed",
            "error": str(e),
            "database": "disconnected"
        } 