"""
Database connection and initialization for Research service.

Manages connections to:
- PostgreSQL with pgvector for document storage and vector search
- Redis for caching and session management  
- Neo4j for knowledge graph storage
"""

import asyncio
import logging
from typing import Optional
import asyncpg
import redis.asyncio as redis
from neo4j import AsyncGraphDatabase
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Global connection pools
pg_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None
neo4j_driver: Optional[AsyncGraphDatabase] = None


async def init_postgresql(database_url: str) -> asyncpg.Pool:
    """Initialize PostgreSQL connection pool with pgvector."""
    try:
        pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=30,
            server_settings={
                'application_name': 'plasma_research_service',
                'timezone': 'UTC',
            }
        )
        
        # Test connection and enable pgvector
        async with pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            
            # Create documents table if not exists
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY,
                    title VARCHAR(500) NOT NULL,
                    content TEXT NOT NULL,
                    document_type VARCHAR(50) NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    processing_status VARCHAR(50) DEFAULT 'pending',
                    chunk_count INTEGER DEFAULT 0,
                    embedding_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            # Create document_chunks table with vector support
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id UUID PRIMARY KEY,
                    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    embedding vector(3072),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(document_id, chunk_index)
                )
            ''')
            
            # Create indexes for performance
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_documents_status 
                ON documents(processing_status)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_documents_type 
                ON documents(document_type)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_documents_created 
                ON documents(created_at DESC)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_chunks_document 
                ON document_chunks(document_id)
            ''')
            
            # Create HNSW index for vector similarity search
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding_cosine 
                ON document_chunks 
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ip 
                ON document_chunks 
                USING hnsw (embedding vector_ip_ops)
                WITH (m = 16, ef_construction = 64)
            ''')
            
            # Full-text search index
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_documents_content_fts 
                ON documents 
                USING gin(to_tsvector('english', content))
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_chunks_content_fts 
                ON document_chunks 
                USING gin(to_tsvector('english', content))
            ''')
            
        logger.info("PostgreSQL connection pool initialized with pgvector")
        return pool
        
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        raise


async def init_redis(redis_url: str) -> redis.Redis:
    """Initialize Redis connection for caching."""
    try:
        client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection
        await client.ping()
        
        logger.info("Redis connection established")
        return client
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


async def init_neo4j(neo4j_uri: str, username: str, password: str) -> AsyncGraphDatabase:
    """Initialize Neo4j connection for knowledge graph."""
    try:
        driver = AsyncGraphDatabase.driver(
            neo4j_uri,
            auth=(username, password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=60
        )
        
        # Test connection and create constraints
        async with driver.session() as session:
            # Create constraints for unique entities
            await session.run('''
                CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
                FOR (e:Entity) REQUIRE e.id IS UNIQUE
            ''')
            
            await session.run('''
                CREATE CONSTRAINT entity_name_type IF NOT EXISTS  
                FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE
            ''')
            
            # Create indexes for performance
            await session.run('''
                CREATE INDEX entity_type_idx IF NOT EXISTS
                FOR (e:Entity) ON (e.type)
            ''')
            
            await session.run('''
                CREATE INDEX entity_confidence_idx IF NOT EXISTS
                FOR (e:Entity) ON (e.confidence)
            ''')
            
            await session.run('''
                CREATE INDEX relationship_type_idx IF NOT EXISTS  
                FOR ()-[r:RELATED]->() ON (r.type)
            ''')
            
            await session.run('''
                CREATE INDEX relationship_confidence_idx IF NOT EXISTS
                FOR ()-[r:RELATED]->() ON (r.confidence)  
            ''')
        
        logger.info("Neo4j connection established with knowledge graph schema")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise


async def init_database():
    """Initialize all database connections."""
    global pg_pool, redis_client, neo4j_driver
    
    from .config import get_settings
    settings = get_settings()
    
    # Initialize PostgreSQL
    if settings.database_url:
        pg_pool = await init_postgresql(settings.database_url)
    else:
        logger.warning("PostgreSQL database URL not configured")
    
    # Initialize Redis (optional)
    if settings.redis_url:
        try:
            redis_client = await init_redis(settings.redis_url)
        except Exception as e:
            logger.warning(f"Redis connection failed, continuing without cache: {e}")
    
    # Initialize Neo4j (optional)
    if settings.neo4j_uri and settings.neo4j_username and settings.neo4j_password:
        try:
            neo4j_driver = await init_neo4j(
                settings.neo4j_uri,
                settings.neo4j_username,
                settings.neo4j_password
            )
        except Exception as e:
            logger.warning(f"Neo4j connection failed, continuing without knowledge graph: {e}")


async def close_database():
    """Close all database connections."""
    global pg_pool, redis_client, neo4j_driver
    
    if pg_pool:
        await pg_pool.close()
        logger.info("PostgreSQL connection pool closed")
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")
    
    if neo4j_driver:
        await neo4j_driver.close()
        logger.info("Neo4j connection closed")


@asynccontextmanager
async def get_db_connection():
    """Get PostgreSQL database connection from pool."""
    if not pg_pool:
        raise RuntimeError("PostgreSQL connection pool not initialized")
    
    async with pg_pool.acquire() as conn:
        yield conn


@asynccontextmanager
async def get_redis_connection():
    """Get Redis connection."""
    if not redis_client:
        raise RuntimeError("Redis connection not initialized")
    
    yield redis_client


@asynccontextmanager  
async def get_neo4j_session():
    """Get Neo4j database session."""
    if not neo4j_driver:
        raise RuntimeError("Neo4j driver not initialized")
    
    async with neo4j_driver.session() as session:
        yield session


# Health check functions
async def check_postgresql_health() -> bool:
    """Check PostgreSQL connection health."""
    try:
        if not pg_pool:
            return False
        
        async with pg_pool.acquire() as conn:
            result = await conn.fetchval('SELECT 1')
            return result == 1
    except Exception:
        return False


async def check_redis_health() -> bool:
    """Check Redis connection health."""
    try:
        if not redis_client:
            return False
        
        await redis_client.ping()
        return True
    except Exception:
        return False


async def check_neo4j_health() -> bool:
    """Check Neo4j connection health."""
    try:
        if not neo4j_driver:
            return False
        
        async with neo4j_driver.session() as session:
            result = await session.run('RETURN 1 as test')
            record = await result.single()
            return record['test'] == 1
    except Exception:
        return False


# Utility functions
async def execute_with_retry(func, max_retries: int = 3, delay: float = 1.0):
    """Execute database function with retry logic."""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            logger.warning(f"Database operation failed (attempt {attempt + 1}): {e}")
            await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff