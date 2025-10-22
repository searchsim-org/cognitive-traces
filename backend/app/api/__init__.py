"""
API routes module
"""

from fastapi import APIRouter
from app.api.endpoints import annotations, sessions, models, export

router = APIRouter()

router.include_router(annotations.router, prefix="/annotations", tags=["annotations"])
router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
router.include_router(models.router, prefix="/models", tags=["models"])
router.include_router(export.router, prefix="/export", tags=["export"])

