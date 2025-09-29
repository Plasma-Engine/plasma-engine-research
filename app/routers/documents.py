"""Document management API routes."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from ..models import DocumentResponse, DocumentCreateRequest

router = APIRouter()

@router.get("/", response_model=List[DocumentResponse])
async def list_documents():
    """List all documents."""
    return []

@router.post("/", response_model=DocumentResponse)
async def create_document(document: DocumentCreateRequest):
    """Create a new document."""
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/{document_id}", response_model=DocumentResponse)  
async def get_document(document_id: str):
    """Get a specific document."""
    raise HTTPException(status_code=501, detail="Not implemented")