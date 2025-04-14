from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, desc

# Import the existing model and the new schemas
from app.db.models.report import Report, ReportStatus
from app.schemas.report import ReportCreate, ReportUpdate


async def create_report(db: AsyncSession, report_in: ReportCreate) -> Report:
    """
    Create a new report entry using the existing Report model.
    Flushes the session to get the ID but does not commit or refresh.
    """
    # Create the Report object using fields from ReportCreate schema
    db_report = Report(
        title=report_in.title,
        description=report_in.description,
        report_type=report_in.report_type,
        status=report_in.status, # Should be PENDING from schema default
        meta_data=report_in.meta_data,
        organization_id=report_in.organization_id,
        creator_id=report_in.creator_id,
        # template_id=report_in.template_id # Uncomment if template_id is added to ReportCreate
    )
    db.add(db_report)
    # Flush to get the ID assigned, but don't commit here.
    # The transaction should be managed by the request lifecycle/dependency.
    await db.flush()
    await db.refresh(db_report)
    return db_report


async def get_report(db: AsyncSession, report_id: int) -> Optional[Report]:
    """
    Get a single report by its integer ID.
    """
    result = await db.execute(select(Report).filter(Report.id == report_id))
    return result.scalars().first()


async def list_reports(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Report]:
    """
    Get a list of reports, ordered by creation date descending.
    """
    result = await db.execute(
        select(Report)
        .order_by(desc(Report.created_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def update_report(db: AsyncSession, report_id: int, report_update: ReportUpdate) -> Optional[Report]:
    """
    Update an existing report using the ReportUpdate schema.
    """
    db_report = await get_report(db, report_id)
    if not db_report:
        return None

    # Get update data, excluding unset fields to avoid overwriting with None
    update_data = report_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_report, key, value)

    # Explicitly set updated_at if your model doesn't handle it automatically on update
    # from datetime import datetime, timezone
    # db_report.updated_at = datetime.now(timezone.utc) # Uncomment if needed

    await db.commit()
    await db.refresh(db_report)
    return db_report


async def delete_report(db: AsyncSession, report_id: int) -> bool:
    """
    Delete a report by its integer ID. Returns True if deleted, False otherwise.
    """
    result = await db.execute(delete(Report).where(Report.id == report_id))
    await db.commit()
    return result.rowcount > 0 