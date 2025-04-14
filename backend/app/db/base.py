# This file can serve as a convenience to re-export Base
# Or it can be removed if imports point directly to base_class

from app.db.base_class import Base, metadata

# Optionally, explicitly import models here IF needed for some other purpose,
# but it's generally NOT required for SQLAlchemy metadata discovery if models
# correctly inherit from Base imported from base_class.

# Example (if needed, but likely removable):
# from app.db.models.organization import Organization
# from app.db.models.user import User
# from app.db.models.report import Report

__all__ = ["Base", "metadata"] # Only export Base and metadata 