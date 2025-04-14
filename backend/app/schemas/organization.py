from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, validator

from app.db.models.organization import IntegrationType


# Base organization schema
class OrganizationBase(BaseModel):
    """
    Base schema for organization data.
    """
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    plan_tier: Optional[str] = None


# Schema for creating organizations
class OrganizationCreate(OrganizationBase):
    """
    Schema for creating a new organization.
    """
    name: str
    
    @validator("slug", pre=True, always=True)
    def default_slug(cls, v, values):
        """
        Generate slug from name if not provided.
        """
        if v:
            return v
        if "name" in values:
            import re
            return re.sub(r"\W+", "-", values["name"].lower())
        return None


# Schema for updating organizations
class OrganizationUpdate(OrganizationBase):
    """
    Schema for updating an existing organization.
    """
    pass


# Schema for organization in DB
class OrganizationInDB(OrganizationBase):
    """
    Schema for organization data from the database.
    """
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# Schema for organization response
class OrganizationResponse(OrganizationBase):
    """
    Schema for organization data in API responses.
    """
    id: int
    is_active: bool = True
    created_at: datetime
    user_count: Optional[int] = None
    integration_count: Optional[int] = None
    
    class Config:
        orm_mode = True


# Schema for organization user relation
class OrganizationUserRole(BaseModel):
    """
    Schema for user roles within an organization.
    """
    user_id: int
    organization_id: int
    role: str = "member"


# Integration schemas
class IntegrationBase(BaseModel):
    """
    Base schema for integration data.
    """
    type: IntegrationType
    name: str
    description: Optional[str] = None
    config: Optional[Dict] = None


# Schema for creating integrations
class IntegrationCreate(IntegrationBase):
    """
    Schema for creating a new integration.
    """
    organization_id: int
    credentials: Optional[Dict] = None


# Schema for updating integrations
class IntegrationUpdate(BaseModel):
    """
    Schema for updating an existing integration.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict] = None
    credentials: Optional[Dict] = None


# Schema for integration response
class IntegrationResponse(IntegrationBase):
    """
    Schema for integration data in API responses.
    """
    id: int
    organization_id: int
    is_active: bool = True
    last_sync_at: Optional[str] = None
    created_at: datetime
    
    # Don't include credentials in response
    
    class Config:
        orm_mode = True


# Data source schemas
class DataSourceBase(BaseModel):
    """
    Base schema for data source.
    """
    name: str
    source_type: str
    source_id: str
    config: Optional[Dict] = None


# Schema for creating data sources
class DataSourceCreate(DataSourceBase):
    """
    Schema for creating a new data source.
    """
    integration_id: int


# Schema for updating data sources
class DataSourceUpdate(BaseModel):
    """
    Schema for updating an existing data source.
    """
    name: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict] = None


# Schema for data source response
class DataSourceResponse(DataSourceBase):
    """
    Schema for data source data in API responses.
    """
    id: int
    integration_id: int
    is_active: bool = True
    last_sync_at: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


# List response schemas
class OrganizationListResponse(BaseModel):
    """
    Schema for lists of organizations in API responses.
    """
    organizations: List[OrganizationResponse]
    total: int
    page: int
    page_size: int


class IntegrationListResponse(BaseModel):
    """
    Schema for lists of integrations in API responses.
    """
    integrations: List[IntegrationResponse]
    total: int
    page: int
    page_size: int


class DataSourceListResponse(BaseModel):
    """
    Schema for lists of data sources in API responses.
    """
    data_sources: List[DataSourceResponse]
    total: int
    page: int
    page_size: int 