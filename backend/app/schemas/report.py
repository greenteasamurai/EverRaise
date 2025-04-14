from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Import Enums from the existing model file
from app.db.models.report import ReportStatus, ReportType

# --- Base Schemas ---
class ReportBase(BaseModel):
    title: str = Field(..., example="Q3 Investor Update")
    description: Optional[str] = Field(None, example="Summary of Q3 performance for investors.")
    report_type: ReportType = Field(..., example=ReportType.INVESTOR_UPDATE)
    meta_data: Optional[Dict[str, Any]] = None

# --- Schemas for API Payloads ---
class ReportCreateRequest(BaseModel): # Schema for the API request body for creation
    title: str
    report_type: str # Use string initially from request
    data_sources: Optional[List[str]] = None # Keep this simple for now
    # Assuming org_id and creator_id are handled by auth/dependencies later
    description: Optional[str] = None
    template_id: Optional[int] = None

class ReportCreate(ReportBase): # Internal schema used for CRUD creation
    organization_id: int
    creator_id: int
    report_type: ReportType # Use Enum here
    status: ReportStatus = ReportStatus.PENDING # Start as pending

class ReportUpdate(BaseModel): # Schema for updating after generation
    status: ReportStatus
    content: Optional[str] = None # Matches Text field in model
    meta_data: Optional[Dict[str, Any]] = None
    ai_model_used: Optional[str] = None
    ai_confidence: Optional[float] = None
    generation_time: Optional[float] = None
    token_count: Optional[int] = None
    # Add other relevant fields from the ReportGenerationResponse if needed
    # e.g., summary (might need a summary field in model or store in metadata)
    error_message: Optional[str] = None # Add an error field

    # Ensure at least status is provided
    # @validator('*', pre=True, always=True)
    # def check_not_none(cls, v, field):
    #     if v is None:
    #         raise ValueError(f'{field.name} cannot be None during update')
    #     return v


# --- Schemas for API Responses ---
class ReportRead(ReportBase): # Response for GET /reports/{id}
    id: int
    organization_id: int
    creator_id: int
    template_id: Optional[int] = None
    status: ReportStatus
    content: Optional[str] = None # Matches Text field in model
    meta_data: Optional[Dict[str, Any]] = None
    ai_model_used: Optional[str] = None
    ai_confidence: Optional[float] = None
    generation_time: Optional[float] = None
    token_count: Optional[int] = None
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None # Include error message if present

    class Config:
        from_attributes = True # Pydantic v2 uses this instead of orm_mode


class ReportList(BaseModel): # Response for GET /reports/list
    id: int
    title: str
    report_type: ReportType
    status: ReportStatus
    created_at: datetime
    # Add a summary field if needed/available
    # summary: Optional[str] = None

    class Config:
        from_attributes = True 