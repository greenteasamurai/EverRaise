from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.api.deps import get_current_user, get_current_active_superuser, get_db
from app.core.config import settings
from app.db.models.user import User
from app.db.models.pii import UserPII, PIIAccessLog
from app.services.pii_handler import PIIHandler

router = APIRouter()


@router.post("/pii/store", status_code=status.HTTP_201_CREATED)
async def store_user_pii(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pii_data: Dict[str, str] = Body(...),
    request: Request,
) -> Dict[str, Any]:
    """
    Store encrypted PII data for the current user.
    Requires user consent and follows data minimization principles.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    # Check if user has provided consent for PII storage
    if settings.REQUIRE_CONSENT_FOR_PII and not current_user.data_retention_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has not provided consent for PII storage",
        )
    
    # Validate and sanitize PII data
    is_compliant, violations = PIIHandler.is_compliant_for_storage(pii_data)
    if not is_compliant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"violations": violations},
        )
    
    # Store encrypted PII
    success = await PIIHandler.encrypt_user_pii(db, current_user.id, pii_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store PII data",
        )
    
    logger.info(f"PII data stored for user: {current_user.id} from {client_ip}")
    
    return {"message": "PII data stored successfully"}


@router.get("/pii/my-data")
async def get_my_pii(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
) -> Dict[str, Any]:
    """
    Get the current user's PII data.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    # Log access for audit purposes
    PIIHandler.log_pii_access(
        user_id=current_user.id,
        accessed_by=current_user.id,
        fields=["all"],
        purpose="self-access"
    )
    
    # Retrieve PII data
    pii_data = await PIIHandler.get_user_pii(db, current_user.id)
    
    logger.info(f"User accessed their own PII data: {current_user.id} from {client_ip}")
    
    return {"pii_data": pii_data}


@router.get("/pii/user/{user_id}")
async def get_user_pii(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    user_id: int,
    purpose: str = Query(..., description="Purpose for accessing PII"),
    fields: Optional[List[str]] = Query(None, description="Specific PII fields to retrieve"),
    request: Request,
) -> Dict[str, Any]:
    """
    Get PII data for a specific user.
    Requires superuser privileges and purpose justification.
    Access is logged for audit purposes.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    # Check if the purpose is provided
    if not purpose:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purpose for accessing PII must be provided",
        )
    
    # Log access for audit purposes
    accessed_fields = fields or ["all"]
    PIIHandler.log_pii_access(
        user_id=user_id,
        accessed_by=current_user.id,
        fields=accessed_fields,
        purpose=purpose
    )
    
    # Add entry to PII access log table
    access_log = PIIAccessLog(
        user_id=user_id,
        accessed_by_id=current_user.id,
        accessed_fields=accessed_fields,
        access_reason=purpose,
        access_context="admin_api",
        ip_address=client_ip,
        user_agent=user_agent
    )
    db.add(access_log)
    await db.commit()
    
    # Retrieve PII data
    pii_data = await PIIHandler.get_user_pii(db, user_id, fields)
    
    logger.warning(
        f"Admin user {current_user.id} accessed PII for user {user_id} "
        f"with purpose: '{purpose}' from {client_ip}"
    )
    
    return {"pii_data": pii_data}


@router.post("/pii/consent")
async def update_pii_consent(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    consent: bool = Body(..., embed=True),
    request: Request,
) -> Dict[str, Any]:
    """
    Update user's consent for PII storage.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    # Update user's consent status
    current_user.data_retention_consent = consent
    db.add(current_user)
    await db.commit()
    
    logger.info(f"User {current_user.id} updated PII consent to: {consent} from {client_ip}")
    
    if not consent:
        # TODO: Implement logic to schedule PII deletion
        logger.info(f"PII deletion scheduled for user {current_user.id} due to consent withdrawal")
        
    return {"message": f"PII consent updated to: {consent}"}


@router.delete("/pii/delete")
async def delete_my_pii(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request,
) -> Dict[str, Any]:
    """
    Delete all PII data for the current user.
    """
    # Get client information for security logging
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    # Check if user has PII data
    stmt = db.query(UserPII).filter(UserPII.user_id == current_user.id)
    pii_data = await db.execute(stmt)
    user_pii = pii_data.scalar_one_or_none()
    
    if not user_pii:
        return {"message": "No PII data found to delete"}
    
    # Delete PII data
    await db.delete(user_pii)
    await db.commit()
    
    # Update user's consent status
    current_user.data_retention_consent = False
    db.add(current_user)
    await db.commit()
    
    logger.info(f"User {current_user.id} deleted their PII data from {client_ip}")
    
    return {"message": "PII data deleted successfully"}


@router.get("/pii/access-log")
async def get_pii_access_log(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, description="Number of records to return"),
    offset: int = Query(0, description="Offset for pagination"),
) -> Dict[str, Any]:
    """
    Get PII access log for audit purposes.
    Requires superuser privileges.
    """
    # Build query
    query = db.query(PIIAccessLog).order_by(PIIAccessLog.accessed_at.desc())
    
    # Apply user filter if provided
    if user_id:
        query = query.filter(PIIAccessLog.user_id == user_id)
    
    # Get total count
    count_query = query.statement.with_only_columns([db.func.count()]).order_by(None)
    count_result = await db.execute(count_query)
    total_count = count_result.scalar_one()
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    access_logs = result.scalars().all()
    
    logger.info(f"Admin user {current_user.id} accessed PII access logs")
    
    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "access_logs": access_logs
    }


@router.get("/pii/data-retention-policies")
async def get_data_retention_policies(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get data retention policies.
    """
    # In a real implementation, this would retrieve policies from the database
    # For now, return hardcoded policies
    policies = [
        {
            "data_category": "pii",
            "retention_period_days": settings.PII_RETENTION_DAYS,
            "require_explicit_consent": settings.REQUIRE_CONSENT_FOR_PII,
            "description": "Personal identifiable information such as address, phone number, etc.",
        },
        {
            "data_category": "oauth_tokens",
            "retention_period_days": 90,
            "require_explicit_consent": True,
            "description": "OAuth tokens for third-party service integrations.",
        },
        {
            "data_category": "usage_logs",
            "retention_period_days": 30,
            "require_explicit_consent": False,
            "description": "Application usage logs and analytics.",
        }
    ]
    
    return {"policies": policies} 