"""
Data models for the Research service.

Defines Pydantic models for:
- Document processing and storage
- Vector embeddings and search
- Knowledge graph entities and relationships  
- Search queries and results
- Health checks and service status
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class ServiceStatus(str, Enum):
    """Service health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"


class DocumentType(str, Enum):
    """Supported document types for processing."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "markdown"
    HTML = "html"
    JSON = "json"


class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


# Base Models
class BaseDocument(BaseModel):
    """Base document model with common fields."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    document_type: DocumentType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    """Document chunk for vector storage."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    chunk_index: int
    content: str = Field(..., min_length=1)
    token_count: int = Field(..., ge=1)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Request Models
class DocumentCreateRequest(BaseModel):
    """Request model for document creation."""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    document_type: DocumentType
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('content')
    def validate_content_length(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Content must be at least 10 characters')
        return v


class DocumentUpdateRequest(BaseModel):
    """Request model for document updates."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class BulkDocumentRequest(BaseModel):
    """Request model for bulk document operations."""
    documents: List[DocumentCreateRequest] = Field(..., min_items=1, max_items=100)
    batch_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


class EmbeddingRequest(BaseModel):
    """Request model for generating embeddings."""
    texts: List[str] = Field(..., min_items=1, max_items=100)
    model: Optional[str] = Field(default="text-embedding-3-large")
    batch_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


class VectorSearchRequest(BaseModel):
    """Request model for vector similarity search."""
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None
    include_embeddings: bool = Field(default=False)


class SemanticSearchRequest(BaseModel):
    """Request model for hybrid semantic search."""
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    text_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None
    enable_expansion: bool = Field(default=True)
    
    @validator('vector_weight', 'text_weight')
    def validate_weights(cls, v, values):
        if 'vector_weight' in values:
            if abs((v + values['vector_weight']) - 1.0) > 0.01:
                raise ValueError('vector_weight and text_weight must sum to 1.0')
        return v


class GraphQueryRequest(BaseModel):
    """Request model for knowledge graph queries."""
    query: str = Field(..., min_length=1)
    entity_types: Optional[List[str]] = None
    relationship_types: Optional[List[str]] = None
    max_depth: int = Field(default=2, ge=1, le=5)
    limit: int = Field(default=50, ge=1, le=500)


# Response Models
class DocumentResponse(BaseDocument):
    """Response model for document data."""
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    chunk_count: int = 0
    embedding_count: int = 0
    error_message: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response model for document listings."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class ChunkResponse(DocumentChunk):
    """Response model for document chunks."""
    similarity_score: Optional[float] = None


class EmbeddingResponse(BaseModel):
    """Response model for embeddings."""
    embeddings: List[List[float]]
    model: str
    usage: Dict[str, int]
    batch_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VectorSearchResult(BaseModel):
    """Individual vector search result."""
    document_id: str
    chunk_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_title: Optional[str] = None


class VectorSearchResponse(BaseModel):
    """Response model for vector search."""
    results: List[VectorSearchResult]
    query: str
    total_results: int
    processing_time_ms: float
    search_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class EntityResponse(BaseModel):
    """Response model for knowledge graph entities."""
    id: str
    name: str
    entity_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)
    mentions: int = 0


class RelationshipResponse(BaseModel):
    """Response model for knowledge graph relationships."""
    id: str
    source_entity: str
    target_entity: str
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)
    occurrences: int = 0


class GraphQueryResponse(BaseModel):
    """Response model for graph queries."""
    entities: List[EntityResponse]
    relationships: List[RelationshipResponse]
    query: str
    total_entities: int
    total_relationships: int
    processing_time_ms: float
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class SemanticSearchResult(BaseModel):
    """Individual semantic search result."""
    document_id: str
    chunk_id: Optional[str] = None
    content: str
    title: str
    relevance_score: float
    vector_score: Optional[float] = None
    text_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    entities: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    results: List[SemanticSearchResult]
    query: str
    expanded_query: Optional[str] = None
    total_results: int
    vector_results: int
    text_results: int
    processing_time_ms: float
    search_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ProcessingJobResponse(BaseModel):
    """Response model for background processing jobs."""
    job_id: str
    status: ProcessingStatus
    progress: float = Field(..., ge=0.0, le=1.0)
    message: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_details: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


# Health and Status Models
class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: ServiceStatus
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, Any] = Field(default_factory=dict)
    uptime_seconds: Optional[float] = None


class ServiceMetrics(BaseModel):
    """Service performance metrics."""
    documents_processed: int = 0
    embeddings_generated: int = 0
    searches_performed: int = 0
    average_processing_time_ms: float = 0.0
    average_search_time_ms: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class StatusResponse(BaseModel):
    """Comprehensive service status."""
    health: HealthResponse
    metrics: ServiceMetrics
    active_jobs: int = 0
    queue_size: int = 0
    memory_usage_mb: float = 0.0
    disk_usage_mb: float = 0.0


# Configuration Models
class ProcessingConfig(BaseModel):
    """Document processing configuration."""
    chunk_size: int = Field(default=1024, ge=100, le=4096)
    chunk_overlap: int = Field(default=200, ge=0, le=1024)
    batch_size: int = Field(default=10, ge=1, le=100)
    enable_ocr: bool = False
    extract_metadata: bool = True
    
    @validator('chunk_overlap')
    def validate_chunk_overlap(cls, v, values):
        if 'chunk_size' in values and v >= values['chunk_size']:
            raise ValueError('chunk_overlap must be less than chunk_size')
        return v


class SearchConfig(BaseModel):
    """Search configuration parameters."""
    default_limit: int = Field(default=10, ge=1, le=100)
    max_limit: int = Field(default=100, ge=1, le=1000)
    default_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    enable_query_expansion: bool = True
    enable_highlighting: bool = True
    cache_results: bool = True
    cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)


# Error Models
class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field details."""
    field_errors: List[Dict[str, str]] = Field(default_factory=list)