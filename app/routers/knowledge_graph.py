"""Knowledge graph API routes."""

from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.get("/")
async def get_knowledge_graph():
    """Get knowledge graph."""
    return {"nodes": [], "edges": []}

@router.post("/")
async def create_knowledge_graph():
    """Create knowledge graph."""
    raise HTTPException(status_code=501, detail="Not implemented")