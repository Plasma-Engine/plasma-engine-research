"""Embeddings API routes."""

from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.get("/")
async def list_embeddings():
    """List embeddings."""
    return []

@router.post("/")
async def create_embedding():
    """Create embeddings."""
    raise HTTPException(status_code=501, detail="Not implemented")