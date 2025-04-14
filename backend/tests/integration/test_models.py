from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create a base for test models
TestBase = declarative_base()

# Association table for many-to-many relationship between users and organizations
test_user_organization = Table(
    "test_user_organization",
    TestBase.metadata,
    Column("user_id", Integer, ForeignKey("test_user.id"), primary_key=True),
    Column("organization_id", Integer, ForeignKey("test_organization.id"), primary_key=True),
)

class TestOrganization(TestBase):
    """Test organization model for integration testing."""
    __tablename__ = "test_organization"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(1000), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationship with users
    users = relationship(
        "TestUser",
        secondary=test_user_organization,
        back_populates="organizations"
    )

class TestUser(TestBase):
    """Test user model for integration testing."""
    __tablename__ = "test_user"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Relationships
    organizations = relationship(
        "TestOrganization",
        secondary=test_user_organization,
        back_populates="users"
    )
    
    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.last_name:
            return self.last_name
        return self.email 