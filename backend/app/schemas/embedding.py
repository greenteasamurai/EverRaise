from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, validator

from app.db.models.embedding import ContentType, EmbeddingStatus


# Source content schemas
class SourceContentBase(BaseModel):
    """
    Base schema for source content.
    """
    content_type: ContentType
    external_id: str
    title: Optional[str] = None
    content: str
    meta_data: Optional[Dict[str, Any]] = None
    content_created_at: Optional[datetime] = None
    content_updated_at: Optional[datetime] = None


class SourceContentCreate(SourceContentBase):
    """
    Schema for creating source content.
    """
    organization_id: int
    data_source_id: int


class SourceContentUpdate(BaseModel):
    """
    Schema for updating source content.
    """
    title: Optional[str] = None
    content: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    content_updated_at: Optional[datetime] = None
    embedding_status: Optional[EmbeddingStatus] = None


class SourceContentResponse(SourceContentBase):
    """
    Schema for source content in API responses.
    """
    id: int
    organization_id: int
    data_source_id: int
    embedding_status: EmbeddingStatus
    last_processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# Document embedding schemas
class DocumentEmbeddingBase(BaseModel):
    """
    Base schema for document embeddings.
    """
    chunk_index: int
    chunk_text: str
    embedding_model: str
    vector_id: str
    meta_data: Optional[Dict[str, Any]] = None


class DocumentEmbeddingCreate(DocumentEmbeddingBase):
    """
    Schema for creating document embeddings.
    """
    source_content_id: int


class DocumentEmbeddingUpdate(BaseModel):
    """
    Schema for updating document embeddings.
    """
    meta_data: Optional[Dict[str, Any]] = None


class DocumentEmbeddingResponse(DocumentEmbeddingBase):
    """
    Schema for document embeddings in API responses.
    """
    id: int
    source_content_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# Search query schemas
class SearchQuery(BaseModel):
    """
    Schema for search queries.
    """
    query: str
    filters: Optional[Dict[str, Any]] = None
    organization_id: int
    limit: int = 10
    include_metadata: bool = True
    include_source: bool = True


class SearchQueryLog(BaseModel):
    """
    Schema for logging search queries.
    """
    organization_id: int
    user_id: Optional[int] = None
    query_text: str
    query_vector_id: Optional[str] = None
    search_params: Optional[Dict[str, Any]] = None
    result_count: Optional[int] = None


class SearchResultFeedback(BaseModel):
    """
    Schema for search result feedback.
    """
    search_query_id: int
    was_relevant: Optional[bool] = None
    user_feedback: Optional[str] = None
    result_feedbacks: Optional[List[Dict[str, Any]]] = None


class SearchResultItem(BaseModel):
    """
    Schema for individual search result items.
    """
    chunk_text: str
    similarity_score: float
    meta_data: Optional[Dict[str, Any]] = None
    source_id: int
    source_type: ContentType
    source_title: Optional[str] = None
    external_id: Optional[str] = None


class SearchResponse(BaseModel):
    """
    Schema for search responses.
    """
    query: str
    results: List[SearchResultItem]
    total_found: int
    search_id: int
    filters_applied: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None


# Embedding processing schemas
class EmbeddingProcessRequest(BaseModel):
    """
    Schema for requesting embedding processing.
    """
    content_ids: List[int]
    force_reprocess: bool = False
    embedding_model: Optional[str] = None


class EmbeddingProcessResponse(BaseModel):
    """
    Schema for embedding processing response.
    """
    total_processed: int
    failed_ids: List[int] = []
    status: str
    job_id: Optional[str] = None


# List response schemas
class SourceContentListResponse(BaseModel):
    """
    Schema for lists of source content in API responses.
    """
    items: List[SourceContentResponse]
    total: int
    page: int
    page_size: int


class DocumentEmbeddingListResponse(BaseModel):
    """
    Schema for lists of document embeddings in API responses.
    """
    items: List[DocumentEmbeddingResponse]
    total: int
    page: int
    page_size: int 