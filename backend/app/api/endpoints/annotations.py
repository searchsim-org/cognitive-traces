"""
Annotation endpoints for cognitive trace generation
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
from app.schemas.annotation import AnnotationRequest, AnnotationResponse, BatchAnnotationRequest
from app.services.annotation_service import AnnotationService

router = APIRouter()
annotation_service = AnnotationService()


@router.post("/annotate", response_model=AnnotationResponse)
async def annotate_session(request: AnnotationRequest):
    """
    Annotate a single user session with cognitive traces using the multi-agent framework.
    
    The process involves three agents:
    - Analyst (Claude 3.5 Sonnet): Initial analysis and label proposal
    - Critic (GPT-4o): Challenge and review the analyst's conclusions
    - Judge (GPT-4o): Final decision and justification
    """
    try:
        result = await annotation_service.annotate_session(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-annotate")
async def batch_annotate(request: BatchAnnotationRequest):
    """
    Submit a batch of sessions for annotation. This is processed asynchronously.
    Returns a job_id to track progress.
    """
    try:
        job_id = await annotation_service.batch_annotate(request)
        return {"job_id": job_id, "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_type: str = "aol"
):
    """
    Upload a dataset file (CSV or JSON) for annotation.
    Supported dataset types: aol, stackoverflow, movielens, custom
    """
    try:
        result = await annotation_service.upload_dataset(file, dataset_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a batch annotation job.
    """
    try:
        status = await annotation_service.get_job_status(job_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

