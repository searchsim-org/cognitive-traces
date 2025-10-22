"""
Export endpoints for annotated data
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional

router = APIRouter()


@router.get("/csv")
async def export_csv(
    dataset: Optional[str] = None,
    session_ids: Optional[str] = Query(None, description="Comma-separated session IDs")
):
    """
    Export annotations as CSV file.
    """
    # TODO: Implement CSV export
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/json")
async def export_json(
    dataset: Optional[str] = None,
    session_ids: Optional[str] = Query(None, description="Comma-separated session IDs")
):
    """
    Export annotations as JSON file.
    """
    # TODO: Implement JSON export
    raise HTTPException(status_code=501, detail="Not implemented yet")

