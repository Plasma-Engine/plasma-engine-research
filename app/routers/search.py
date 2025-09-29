"""Search API routes."""

from fastapi import APIRouter, HTTPException
from typing import List, Optional

router = APIRouter()

@router.get("/")
async def search(q: str, limit: Optional[int] = 10):
    """Semantic search."""
    return {"query": q, "results": [], "limit": limit}

@router.post("/")
async def advanced_search():
    """Advanced search."""
    raise HTTPException(status_code=501, detail="Not implemented")