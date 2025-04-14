# Import models so they can be discovered by SQLAlchemy
from app.db.models.user import User

# Export models
__all__ = ["User"] 