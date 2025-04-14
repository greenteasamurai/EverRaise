from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, 
    String, Table, Text, JSON
)
from sqlalchemy.orm import Mapped, relationship

from app.db.base_class import Base


class ContentType(str, PyEnum):
    """
    Types of content that can be embedded.
    """
    EMAIL = "email"
    SLACK_MESSAGE = "slack_message"
    TEAMS_MESSAGE = "teams_message"
    MEETING_TRANSCRIPT = "meeting_transcript"
    DOCUMENT = "document"
    JIRA_TICKET = "jira_ticket"
    ASANA_TASK = "asana_task"
    NOTION_PAGE = "notion_page"
    CUSTOM = "custom"


class EmbeddingStatus(str, PyEnum):
    """
    Status of embedding processing.
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceContent(Base):
    """
    Source content from integrations that is processed for embeddings.
    """
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False)
    data_source_id = Column(Integer, ForeignKey("data_source.id"), nullable=False)
    
    # Content information
    content_type = Column(Enum(ContentType), nullable=False)
    external_id = Column(String(255), nullable=False)  # ID from original source
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    content_created_at = Column(DateTime, nullable=True)
    content_updated_at = Column(DateTime, nullable=True)
    
    # Processing status
    embedding_status = Column(Enum(EmbeddingStatus), default=EmbeddingStatus.PENDING)
    last_processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    
    data_source: Mapped["DataSource"] = relationship("DataSource")
    
    embeddings: Mapped[List["DocumentEmbedding"]] = relationship(
        "DocumentEmbedding",
        back_populates="source_content",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<SourceContent {self.id} ({self.content_type})>"


class DocumentEmbedding(Base):
    """
    Document chunks and their embeddings.
    """
    source_content_id = Column(Integer, ForeignKey("source_content.id"), nullable=False)
    
    # Embedding information
    chunk_index = Column(Integer, nullable=False)  # Position in the document
    chunk_text = Column(Text, nullable=False)  # The actual chunk of text
    embedding_model = Column(String(100), nullable=False)  # Model used for embedding
    vector_id = Column(String(255), nullable=False)  # ID in vector database
    
    # Metadata for retrieval
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    source_content: Mapped["SourceContent"] = relationship(
        "SourceContent",
        back_populates="embeddings",
    )
    
    def __repr__(self):
        return f"<DocumentEmbedding {self.id} (chunk {self.chunk_index})>"


class SearchQuery(Base):
    """
    Log of search queries for analytics and improvement.
    """
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    
    # Query information
    query_text = Column(Text, nullable=False)
    query_vector_id = Column(String(255), nullable=True)  # If query was vectorized
    
    # Search parameters
    search_params = Column(JSON, nullable=True)
    result_count = Column(Integer, nullable=True)
    
    # Result feedback
    was_relevant = Column(Boolean, nullable=True)
    user_feedback = Column(Text, nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    
    user: Mapped[Optional["User"]] = relationship("User")
    
    results: Mapped[List["SearchResult"]] = relationship(
        "SearchResult",
        back_populates="search_query",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<SearchQuery {self.id}: '{self.query_text[:50]}...'>"


class SearchResult(Base):
    """
    Individual search results returned for a query.
    """
    search_query_id = Column(Integer, ForeignKey("search_query.id"), nullable=False)
    embedding_id = Column(Integer, ForeignKey("document_embedding.id"), nullable=False)
    
    # Result metrics
    similarity_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    
    # User feedback on this specific result
    was_helpful = Column(Boolean, nullable=True)
    
    # Relationships
    search_query: Mapped["SearchQuery"] = relationship(
        "SearchQuery",
        back_populates="results",
    )
    
    embedding: Mapped["DocumentEmbedding"] = relationship("DocumentEmbedding")
    
    def __repr__(self):
        return f"<SearchResult {self.id} (rank: {self.rank}, score: {self.similarity_score})>" 