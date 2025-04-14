import re
from typing import Any, Dict, Type

from sqlalchemy import Column, DateTime, Integer, MetaData, func
from sqlalchemy.ext.declarative import as_declarative, declared_attr

# SQLAlchemy naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


@as_declarative(metadata=metadata)
class Base:
    """
    Base class for all SQLAlchemy models.
    Provides common columns and methods.
    """

    # Primary key for all tables
    id = Column(Integer, primary_key=True, index=True)
    
    # Timestamps for creation and updates
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Import models AFTER Base is defined so they register with its metadata
# This is crucial for Base.metadata.create_all to work correctly
try:
    from app.db.models.organization import Organization, Integration, DataSource
    from app.db.models.user import User # user_organization table defined here too
    from app.db.models.report import Report, ReportTemplate, ReportSection, ReportVersion, report_data_source
    # Assuming embedding models exist and are needed:
    # from app.db.models.embedding import SourceContent, DocumentEmbedding, SearchQuery, SearchResult
except ImportError as e:
    # Log or print a warning if models can't be imported, e.g., during early dev
    print(f"Warning during model import for metadata registration: {e}") 