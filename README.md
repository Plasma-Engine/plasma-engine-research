# Plasma Engine Research

## Overview

**Plasma Engine Research** is the AI-powered research and knowledge management service. It implements:

- 🧠 **GraphRAG System**: Graph-based knowledge representation and retrieval
- 🔍 **Semantic Search**: Vector embeddings with pgvector/Pinecone
- 📚 **Document Processing**: Multi-format ingestion and parsing
- 🔗 **Entity Extraction**: NER and relationship mapping
- 💡 **Knowledge Synthesis**: AI-powered insights and summaries
- 🎯 **Query Understanding**: Intent classification and query expansion

## Tech Stack

- **Language**: Python 3.11
- **Framework**: FastAPI
- **AI/ML**: LangChain, LlamaIndex, OpenAI SDK
- **Graph DB**: Neo4j for knowledge graphs
- **Vector DB**: pgvector / Pinecone
- **Queue**: Celery + Redis for async processing
- **Storage**: S3-compatible for documents

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload

# Run tests
pytest

# Start Celery worker
celery -A app.tasks worker --loglevel=info
```

## Architecture

```
Documents → Ingestion → Processing → Knowledge Graph → Query Engine
                ↓           ↓              ↓
            Embeddings   Entities    Relationships
```

## Key Features

- **Multi-modal RAG**: Text, code, images, tables
- **Incremental Learning**: Continuous knowledge base updates
- **Citation Tracking**: Source attribution for all responses
- **Privacy-First**: Local embeddings option, data isolation

## Development

See [Development Handbook](../plasma-engine-shared/docs/development-handbook.md) for guidelines.

## CI/CD

This repository uses GitHub Actions for CI/CD. All PRs are automatically:
- Linted and tested
- Security scanned
- Reviewed by CodeRabbit

See `.github/workflows/ci.yml` for details.