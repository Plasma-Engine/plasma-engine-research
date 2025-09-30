"""FastAPI application bootstrap for the Research service.

The goal of this file is to provide a production-ready Research service
with advanced RAG (Retrieval-Augmented Generation) capabilities including:
- Document ingestion and processing
- Vector embeddings with pgvector
- Knowledge graph construction with Neo4j
- Hybrid semantic search
- GraphRAG query processing
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio
from typing import List, Optional, Dict, Any
import logging

from .config import ResearchSettings, get_settings
from .routers import documents, embeddings, knowledge_graph, search
from .services.document_processor import DocumentProcessor
from .services.vector_store import VectorStore
from .services.knowledge_graph import KnowledgeGraphService
from .services.semantic_search import SemanticSearchService
from .database import init_database, close_database
from .models import HealthResponse, ServiceStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services (initialized at startup)
document_processor: DocumentProcessor = None
vector_store: VectorStore = None
knowledge_graph: KnowledgeGraphService = None
semantic_search: SemanticSearchService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events."""
    global document_processor, vector_store, knowledge_graph, semantic_search
    
    logger.info("Starting Research Service initialization...")
    
    try:
        # Initialize database connections
        await init_database()
        logger.info("Database connections established")
        
        # Initialize core services
        settings = get_settings()
        
        document_processor = DocumentProcessor(settings)
        await document_processor.initialize()
        logger.info("Document processor initialized")
        
        vector_store = VectorStore(settings)
        await vector_store.initialize()
        logger.info("Vector store initialized")
        
        knowledge_graph = KnowledgeGraphService(settings)
        await knowledge_graph.initialize()
        logger.info("Knowledge graph service initialized")
        
        semantic_search = SemanticSearchService(
            vector_store=vector_store,
            knowledge_graph=knowledge_graph,
            settings=settings
        )
        await semantic_search.initialize()
        logger.info("Semantic search service initialized")
        
        logger.info("🔬 Research Service successfully initialized!")
        
    except Exception as e:
        logger.error(f"Failed to initialize Research Service: {e}")
        raise
    
    yield  # Application runs here
    
    # Cleanup on shutdown
    logger.info("Shutting down Research Service...")
    
    if semantic_search:
        await semantic_search.close()
    if knowledge_graph:
        await knowledge_graph.close()
    if vector_store:
        await vector_store.close()
    if document_processor:
        await document_processor.close()
        
    await close_database()
    logger.info("Research Service shutdown complete")


def create_app(settings: ResearchSettings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Parameters
    ----------
    settings:
        Optional override used primarily by tests to inject custom configuration.
    """
    
    # Use provided settings or create new instance
    resolved_settings = settings or get_settings()
    
    app = FastAPI(
        title=resolved_settings.app_name,
        description="Advanced Research Service with RAG capabilities",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs" if resolved_settings.environment != "production" else None,
        redoc_url="/redoc" if resolved_settings.environment != "production" else None,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoints
    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health_check() -> HealthResponse:
        """Comprehensive health check including service dependencies."""
        
        status = ServiceStatus.HEALTHY
        checks = {}
        
        try:
            # Check document processor
            if document_processor:
                checks["document_processor"] = await document_processor.health_check()
            else:
                checks["document_processor"] = False
                status = ServiceStatus.DEGRADED
            
            # Check vector store
            if vector_store:
                checks["vector_store"] = await vector_store.health_check()
            else:
                checks["vector_store"] = False
                status = ServiceStatus.DEGRADED
            
            # Check knowledge graph
            if knowledge_graph:
                checks["knowledge_graph"] = await knowledge_graph.health_check()
            else:
                checks["knowledge_graph"] = False
                status = ServiceStatus.DEGRADED
            
            # Check semantic search
            if semantic_search:
                checks["semantic_search"] = await semantic_search.health_check()
            else:
                checks["semantic_search"] = False
                status = ServiceStatus.DEGRADED
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            status = ServiceStatus.UNHEALTHY
            checks["error"] = str(e)
        
        return HealthResponse(
            status=status,
            service=resolved_settings.app_name,
            version="2.0.0",
            checks=checks
        )
    
    @app.get("/ready", tags=["health"])
    async def readiness_check():
        """Kubernetes readiness probe."""
        health = await health_check()
        
        if health.status == ServiceStatus.UNHEALTHY:
            raise HTTPException(status_code=503, detail="Service not ready")
        
        return {"status": "ready"}
    
    # Include API routers
    app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
    app.include_router(embeddings.router, prefix="/api/v1/embeddings", tags=["embeddings"])
    app.include_router(knowledge_graph.router, prefix="/api/v1/knowledge", tags=["knowledge_graph"])
    app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception: {exc}")
        return HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    
    return app


# Create the app instance
app = create_app(get_settings())


# Dependency injection for services
def get_document_processor() -> DocumentProcessor:
    """Get document processor service."""
    if not document_processor:
        raise HTTPException(status_code=503, detail="Document processor not initialized")
    return document_processor


def get_vector_store() -> VectorStore:
    """Get vector store service."""
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    return vector_store


def get_knowledge_graph() -> KnowledgeGraphService:
    """Get knowledge graph service."""
    if not knowledge_graph:
        raise HTTPException(status_code=503, detail="Knowledge graph not initialized")
    return knowledge_graph


def get_semantic_search() -> SemanticSearchService:
    """Get semantic search service."""
    if not semantic_search:
        raise HTTPException(status_code=503, detail="Semantic search not initialized")
    return semantic_search


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
        log_level="info"
    )

