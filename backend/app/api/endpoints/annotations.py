"""
Annotation endpoints for cognitive trace generation
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
from app.schemas.annotation import AnnotationRequest, AnnotationResponse, BatchAnnotationRequest
from app.services.annotation_service import AnnotationService
from datetime import datetime

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


@router.get("/dataset/{dataset_id}")
async def get_dataset_info(dataset_id: str, page: int = 1, limit: int = 10):
    """
    Get dataset information with paginated session preview.
    """
    try:
        info = await annotation_service.get_dataset_info(dataset_id, page, limit)
        return info
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")


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


@router.post("/start-job")
async def start_annotation_job(request: Dict[str, Any]):
    """
    Start annotation job for an uploaded dataset.
    
    Required fields:
    - dataset_id: ID from upload endpoint
    - llm_config: Configuration for LLM models and API keys
    - dataset_name: Name for output files (optional)
    """
    try:
        dataset_id = request.get('dataset_id')
        llm_config = request.get('llm_config', {})
        dataset_name = request.get('dataset_name', 'dataset')
        
        if not dataset_id:
            raise HTTPException(status_code=400, detail="dataset_id is required")
        
        resume_job_id = request.get('resume_job_id')
        result = await annotation_service.start_annotation_job(
            dataset_id, llm_config, dataset_name, resume_job_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}/session/{session_id}/log")
async def get_session_log(job_id: str, session_id: str):
    """
    Get detailed agent interaction log for a specific session.
    """
    try:
        log = await annotation_service.get_session_log(job_id, session_id)
        if log is None:
            raise HTTPException(status_code=404, detail=f"Log not found for session {session_id}")
        return log
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/job/{job_id}/stop")
async def stop_job(job_id: str):
    """
    Request a job to stop gracefully. The job will complete the current session
    and then stop. Progress is saved via checkpoint system for later resumption.
    """
    try:
        result = await annotation_service.stop_job(job_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/job/{job_id}/session/{session_id}/resolve")
async def resolve_session_annotation(job_id: str, session_id: str, payload: Dict[str, Any]):
    """
    Resolve flagged annotations for a session by applying a user-selected label.
    Overwrites cognitive labels for flagged events and updates output/logs.
    """
    try:
        from app.services.annotation_orchestrator import AnnotationOrchestrator
        label = payload.get('label')
        note = payload.get('note', '')
        if not label:
            raise HTTPException(status_code=400, detail="label is required")

        # Locate orchestrator
        if job_id not in annotation_service.active_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        orchestrator: AnnotationOrchestrator = annotation_service.active_jobs[job_id]

        # Load existing log
        log = orchestrator.get_session_log(session_id, job_id)
        if not log:
            raise HTTPException(status_code=404, detail=f"Log not found for session {session_id}")

        # Overwrite flagged events' cognitive_label with user label and bump version
        for ev in log.get('events', []):
            if ev.get('flagged_for_review', False):
                ev['cognitive_label'] = label
                ev['user_override'] = True
                ev['user_note'] = note
                # Increment version (default from 1)
                try:
                  ev['override_version'] = int(ev.get('override_version', 1)) + 1
                except Exception:
                  ev['override_version'] = 2
                ev['override_timestamp'] = datetime.now().isoformat()

        # Persist back to log file
        orchestrator.session_logs[session_id] = log
        from pathlib import Path
        import json
        log_file = orchestrator.output_dir / job_id / "logs" / f"{session_id}_log.json"
        with open(log_file, 'w') as f:
            json.dump(log, f, indent=2)

        # Also update CSV rows by appending corrected events
        # Note: For simplicity we append corrected rows; a full replacement would require rewriting CSV.
        corrected_result = {
            'session_id': session_id,
            'annotated_events': log.get('events', [])
        }
        output_file = orchestrator.output_dir / job_id / f"{payload.get('dataset_name', 'dataset')}_cognitive_traces.csv"
        if output_file.exists():
            orchestrator._append_to_csv(output_file, corrected_result)

        return {"status": "ok", "session_id": session_id, "label": label}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

