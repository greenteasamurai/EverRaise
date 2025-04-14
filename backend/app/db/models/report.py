from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, 
    String, Table, Text, JSON
)
from sqlalchemy.orm import Mapped, relationship

from app.db.base_class import Base


class ReportType(str, PyEnum):
    """
    Types of reports supported by the system.
    """
    INVESTOR_UPDATE = "investor_update"
    BUSINESS_REVIEW = "business_review"
    KNOWLEDGE_SUMMARY = "knowledge_summary"
    CUSTOM = "custom"


class ReportStatus(str, PyEnum):
    """
    Status of report generation.
    """
    DRAFT = "draft"
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    PUBLISHED = "published"


# Association table for reports and data sources
report_data_source = Table(
    "report_data_source",
    Base.metadata,
    Column("report_id", Integer, ForeignKey("report.id"), primary_key=True),
    Column("data_source_id", Integer, ForeignKey("data_source.id"), primary_key=True),
)


class ReportTemplate(Base):
    """
    Templates for report generation.
    """
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)
    
    # Template structure
    structure = Column(JSON, nullable=False)
    default_sections = Column(JSON, nullable=True)
    
    # AI configuration
    llm_settings = Column(JSON, nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="template",
    )
    
    def __repr__(self):
        return f"<ReportTemplate {self.name}>"


class Report(Base):
    """
    Report model for storing generated reports.
    """
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("report_template.id"), nullable=True)
    
    # Basic information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)
    
    # Generation status
    status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT, nullable=False)
    scheduled_for = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    
    # Report content
    content = Column(Text, nullable=True)  # Markdown or HTML content
    meta_data = Column(JSON, nullable=True)  # Renamed from metadata
    
    # AI information
    ai_model_used = Column(String(100), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_reasoning = Column(Text, nullable=True)
    
    # Generation metrics
    generation_time = Column(Float, nullable=True)  # in seconds
    token_count = Column(Integer, nullable=True)
    
    # Visibility
    is_public = Column(Boolean(), default=False)
    access_code = Column(String(100), nullable=True)  # For sharing
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="reports",
    )
    
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="reports",
    )
    
    template: Mapped[Optional["ReportTemplate"]] = relationship(
        "ReportTemplate",
        back_populates="reports",
    )
    
    data_sources: Mapped[List["DataSource"]] = relationship(
        secondary=report_data_source,
    )
    
    sections: Mapped[List["ReportSection"]] = relationship(
        "ReportSection",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    
    versions: Mapped[List["ReportVersion"]] = relationship(
        "ReportVersion",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<Report {self.title} ({self.status})>"


class ReportSection(Base):
    """
    Sections within a report.
    """
    report_id = Column(Integer, ForeignKey("report.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    order = Column(Integer, default=0, nullable=False)
    
    # Section metadata
    section_type = Column(String(50), nullable=False)  # text, chart, table, etc.
    meta_data = Column(JSON, nullable=True)  # Renamed from metadata
    
    # AI information
    ai_confidence = Column(Float, nullable=True)
    sources = Column(JSON, nullable=True)  # Sources used for this section
    
    # Relationship
    report: Mapped["Report"] = relationship(
        "Report",
        back_populates="sections",
    )
    
    def __repr__(self):
        return f"<ReportSection {self.title}>"


class ReportVersion(Base):
    """
    Version history for reports.
    """
    report_id = Column(Integer, ForeignKey("report.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)  # Renamed from metadata
    comment = Column(Text, nullable=True)
    
    # Relationships
    report: Mapped["Report"] = relationship(
        "Report",
        back_populates="versions",
    )
    
    created_by: Mapped["User"] = relationship("User")
    
    def __repr__(self):
        return f"<ReportVersion {self.report_id}-v{self.version}>" 