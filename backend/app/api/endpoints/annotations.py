"""
Annotation endpoints for cognitive trace generation
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from typing import List, Dict, Any, Optional
from app.schemas.annotation import (
    AnnotationRequest, 
    AnnotationResponse, 
    BatchAnnotationRequest,
    LLMConfigSchema
)
from app.services.annotation_service import AnnotationService
from datetime import datetime
from pydantic import BaseModel

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


class StartJobRequest(BaseModel):
    """Request to start an annotation job"""
    dataset_id: str
    llm_config: LLMConfigSchema
    dataset_name: str = "dataset"
    resume_job_id: Optional[str] = None


@router.post("/start-job")
async def start_annotation_job(request: StartJobRequest):
    """
    Start annotation job for an uploaded dataset.
    
    Required fields:
    - dataset_id: ID from upload endpoint
    - llm_config: Configuration for LLM models, API keys, and processing strategies
    - dataset_name: Name for output files (optional)
    - resume_job_id: Job ID to resume from checkpoint (optional)
    """
    try:
        result = await annotation_service.start_annotation_job(
            request.dataset_id, 
            request.llm_config.model_dump(), 
            request.dataset_name, 
            request.resume_job_id
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


class ResumeJobRequest(BaseModel):
    """Request to resume an annotation job"""
    dataset_id: Optional[str] = None
    llm_config: Optional[LLMConfigSchema] = None


@router.post("/job/{job_id}/resume")
async def resume_job(job_id: str, request: Optional[ResumeJobRequest] = None):
    """
    Resume a paused or stopped annotation job from its checkpoint.
    
    If the original dataset is not in memory, you can provide:
    - dataset_id: ID from a freshly uploaded dataset
    - llm_config: LLM configuration to use (optional, will use default if not provided)
    
    The job will continue processing remaining sessions from where it left off.
    """
    try:
        dataset_id = request.dataset_id if request else None
        llm_config = request.llm_config.model_dump() if request and request.llm_config else None
        result = await annotation_service.resume_job(job_id, dataset_id, llm_config)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/config/default")
async def get_default_config():
    """
    Get default LLM configuration with all available options and their descriptions.
    Use this as a starting point for customization.
    """
    default_config = LLMConfigSchema()
    return {
        "config": default_config.model_dump(),
        "schema": LLMConfigSchema.model_json_schema(),
        "strategies": {
            "truncate": {
                "name": "Truncate Content",
                "description": "Processes all events but truncates content length based on session size",
                "best_for": "Most sessions, balances accuracy and cost",
                "pros": ["Sees entire session context", "Good for understanding full journey"],
                "cons": ["May lose detail in long content"]
            },
            "sliding_window": {
                "name": "Sliding Window",
                "description": "Only processes the last N events (configurable window_size)",
                "best_for": "Very long sessions (>100 events)",
                "pros": ["Consistent processing time", "Full detail for recent events"],
                "cons": ["Loses early session context", "May miss important patterns"]
            },
            "full": {
                "name": "Full Processing",
                "description": "Processes all events with full content (may hit token limits)",
                "best_for": "Short sessions with critical detail",
                "pros": ["Maximum detail preserved", "Best accuracy for short sessions"],
                "cons": ["Expensive", "May fail on very long sessions"]
            }
        }
    }


@router.get("/config/prompts")
async def get_default_prompts():
    """
    Get default prompts for each agent (Analyst, Critic, Judge).
    Copy and modify these for custom prompt overrides.
    """
    from app.services.llm_agents import LABEL_SCHEMA
    
    analyst_prompt = """You are an expert behavioral analyst specializing in Information Foraging Theory. Your task is to analyze user behavior and assign cognitive labels to each event in the session.

{LABEL_SCHEMA}

## Session to Analyze:
{events_str}

## Your Task:
For EACH event in the session, provide:
1. The most appropriate cognitive label
2. Step-by-step justification for your choice
3. Confidence score (0.0-1.0)

## Output Format (JSON):
Return a JSON array with one object per event:
```json
[
  {{
    "event_id": "...",
    "label": "FollowingScent",
    "justification": "Step-by-step reasoning...",
    "confidence": 0.85
  }}
]
```

Provide ONLY the JSON array, no additional text."""
    
    critic_prompt = """You are a critical reviewer specializing in Information Foraging Theory. Your role is to challenge and review the Analyst's cognitive label assignments.

{LABEL_SCHEMA}

## Analyst's Analysis:
{analysis_str}

## Your Task:
For EACH event, either:
1. AGREE with the Analyst's label and provide brief supporting argument
2. DISAGREE and propose a different label with counter-argument

Be thorough and question assumptions. Look for alternative explanations.

## Output Format (JSON):
```json
[
  {{
    "event_id": "...",
    "agreement": "agree" | "disagree",
    "label": "FollowingScent",
    "justification": "Reasoning for agreement or alternative explanation...",
    "confidence": 0.80
  }}
]
```

Provide ONLY the JSON array, no additional text."""
    
    judge_prompt = """You are the final arbiter in a multi-agent cognitive labeling system. Your role is to synthesize the Analyst's and Critic's perspectives and make the final decision.

{LABEL_SCHEMA}

## Agent Deliberations:
{deliberation_str}

## Your Task:
For EACH event, provide:
1. Your FINAL cognitive label decision
2. Comprehensive justification synthesizing both perspectives
3. Final confidence score
4. Flag for human review if there's significant disagreement

## Output Format (JSON):
```json
[
  {{
    "event_id": "...",
    "final_label": "FollowingScent",
    "justification": "Comprehensive synthesis of all perspectives...",
    "confidence": 0.87,
    "flag_for_review": false,
    "disagreement_score": 0.15
  }}
]
```

Provide ONLY the JSON array, no additional text."""
    
    return {
        "analyst_prompt": analyst_prompt,
        "critic_prompt": critic_prompt,
        "judge_prompt": judge_prompt,
        "label_schema": LABEL_SCHEMA,
        "notes": {
            "placeholders": {
                "{LABEL_SCHEMA}": "Automatically replaced with cognitive label definitions",
                "{events_str}": "Automatically replaced with formatted session events (Analyst)",
                "{analysis_str}": "Automatically replaced with analyst decisions (Critic)",
                "{deliberation_str}": "Automatically replaced with all agent decisions (Judge)"
            },
            "customization_tips": [
                "Keep the JSON output format exactly as shown",
                "You can adjust the tone, level of detail, or add domain-specific guidance",
                "Placeholders are automatically filled - don't remove them",
                "Test with a few sessions before running on full dataset"
            ]
        }
    }


@router.post("/job/{job_id}/session/{session_id}/resolve")
async def resolve_session_annotation(job_id: str, session_id: str, payload: Dict[str, Any]):
    """
    Resolve flagged annotations for a session by applying a user-selected label.
    Overwrites cognitive labels for flagged events and updates output/logs.
    Works with both active and completed jobs.
    """
    try:
        from pathlib import Path
        import json
        from datetime import datetime
        
        label = payload.get('label')
        note = payload.get('note', '')
        dataset_name = payload.get('dataset_name', 'dataset')
        
        if not label:
            raise HTTPException(status_code=400, detail="label is required")

        # Try to get log from active job first
        log = None
        if job_id in annotation_service.active_jobs:
            orchestrator = annotation_service.active_jobs[job_id]
            log = orchestrator.get_session_log(session_id, job_id)
        
        # If not in active jobs, load from saved log file
        if not log:
            log_file = annotation_service.output_dir / job_id / "logs" / f"{session_id}_log.json"
            if not log_file.exists():
                raise HTTPException(status_code=404, detail=f"Log not found for session {session_id} in job {job_id}")
            
            with open(log_file, 'r') as f:
                log = json.load(f)

        # Overwrite flagged events' cognitive_label with user label and add metadata
        updated_count = 0
        flagged_event_ids = []
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
                flagged_event_ids.append(ev.get('event_id'))
                updated_count += 1
        
        print(f"RESOLVE: Session {session_id} - Updated {updated_count} events in log. Flagged IDs: {flagged_event_ids}")

        # Persist back to log file
        log_file = annotation_service.output_dir / job_id / "logs" / f"{session_id}_log.json"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump(log, f, indent=2)

        # Update session log in active orchestrator if available
        if job_id in annotation_service.active_jobs:
            annotation_service.active_jobs[job_id].session_logs[session_id] = log

        # Update CSV file
        output_file = annotation_service.output_dir / job_id / f"{dataset_name}_cognitive_traces.csv"
        if output_file.exists():
            # Read existing CSV, find and update the session rows, then rewrite
            import csv
            rows = []
            fieldnames = None
            updated_csv_count = 0
            session_event_ids_in_csv = set()
            
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row.get('session_id') == session_id:
                        session_event_ids_in_csv.add(row.get('event_id'))
                        # Find corresponding event in the updated log
                        event_id = row.get('event_id')
                        for ev in log.get('events', []):
                            if str(ev.get('event_id')) == str(event_id):
                                # Check if this event was flagged and now has user_override
                                if ev.get('user_override', False):
                                    print(f"CSV UPDATE: Updating event {event_id} with label {label}")
                                    row['cognitive_label'] = label
                                    row['user_override'] = 'True'
                                    # Update override_version and timestamp
                                    row['override_version'] = str(ev.get('override_version', 2))
                                    row['override_timestamp'] = ev.get('override_timestamp', datetime.now().isoformat())
                                    updated_csv_count += 1
                                break
                    rows.append(row)
            
            # Check if there are events in the log that are missing from CSV
            log_event_ids = {str(ev['event_id']) for ev in log.get('events', [])}
            missing_event_ids = log_event_ids - session_event_ids_in_csv
            
            if missing_event_ids:
                print(f"CSV UPDATE: WARNING - {len(missing_event_ids)} events in log but not in CSV: {missing_event_ids}")
                # Add missing events from log to CSV
                for ev in log.get('events', []):
                    if str(ev['event_id']) in missing_event_ids:
                        new_row = {
                            'session_id': session_id,
                            'event_id': ev.get('event_id', ''),
                            'event_timestamp': ev.get('timestamp', ''),
                            'action_type': ev.get('action_type', ''),
                            'content': ev.get('content', ''),
                            'cognitive_label': ev.get('cognitive_label', ''),
                            'analyst_label': ev.get('analyst_label', ''),
                            'analyst_justification': ev.get('analyst_justification', ''),
                            'critic_label': ev.get('critic_label', ''),
                            'critic_agreement': ev.get('critic_agreement', ''),
                            'critic_justification': ev.get('critic_justification', ''),
                            'judge_justification': ev.get('judge_justification', ''),
                            'confidence_score': ev.get('confidence_score', 0),
                            'disagreement_score': ev.get('disagreement_score', 0),
                            'flagged_for_review': str(ev.get('flagged_for_review', False)),
                            'user_override': 'True' if ev.get('user_override', False) else 'False',
                            'override_version': ev.get('override_version', 1),
                            'override_timestamp': ev.get('override_timestamp', '')
                        }
                        rows.append(new_row)
                        if ev.get('user_override', False):
                            updated_csv_count += 1
                            print(f"CSV UPDATE: Added missing event {ev['event_id']} with user override")
            
            # Rewrite CSV with updated data
            if rows and fieldnames:
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                
                print(f"CSV UPDATE: Updated {updated_csv_count} events for session {session_id} in {output_file}")
            else:
                print(f"CSV UPDATE: WARNING - No rows or fieldnames found for {output_file}")

        return {
            "status": "ok",
            "session_id": session_id,
            "label": label,
            "updated_events": updated_count
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

