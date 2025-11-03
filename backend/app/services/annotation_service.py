"""
Service for handling annotation operations
"""

import uuid
import asyncio
import threading
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import UploadFile

from app.schemas.annotation import AnnotationRequest, BatchAnnotationRequest
from app.services.file_parser import FileParser
from app.services.llm_agents import LLMConfig
from app.services.annotation_orchestrator import AnnotationOrchestrator


class AnnotationService:
    """Service for cognitive trace annotation"""
    
    def __init__(self):
        self.file_parser = FileParser()
        self.active_jobs = {}  # job_id -> orchestrator
        self.uploaded_datasets = {}  # temp storage for uploaded data
        
        # Setup paths (same as orchestrator)
        backend_dir = Path(__file__).resolve().parent.parent.parent
        project_root = backend_dir.parent
        self.checkpoint_dir = (project_root / "data" / "checkpoints").resolve()
        self.output_dir = (project_root / "data").resolve()
        self.datasets_dir = (project_root / "data" / "uploaded_datasets").resolve()
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        
        # Load persisted datasets on startup
        self._load_persisted_datasets()
    
    def _persist_dataset(self, dataset_id: str):
        """Persist dataset to disk"""
        try:
            dataset_file = self.datasets_dir / f"{dataset_id}.json"
            with open(dataset_file, 'w') as f:
                json.dump(self.uploaded_datasets[dataset_id], f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to persist dataset {dataset_id}: {e}")
    
    def _load_persisted_datasets(self):
        """Load persisted datasets from disk on startup"""
        try:
            for dataset_file in self.datasets_dir.glob("*.json"):
                try:
                    with open(dataset_file, 'r') as f:
                        dataset_id = dataset_file.stem
                        self.uploaded_datasets[dataset_id] = json.load(f)
                        print(f"Loaded persisted dataset: {dataset_id}")
                except Exception as e:
                    print(f"Warning: Failed to load dataset {dataset_file}: {e}")
        except Exception as e:
            print(f"Warning: Failed to load persisted datasets: {e}")
    
    async def upload_dataset(self, file: UploadFile, dataset_type: str = "custom") -> Dict[str, Any]:
        """Upload and parse dataset file"""
        try:
            # Read file content
            content = await file.read()
            
            # Parse file
            parsed_data = await self.file_parser.parse_file(content, file.filename)
            
            # Generate dataset ID
            dataset_id = str(uuid.uuid4())
            
            # Store parsed data temporarily
            self.uploaded_datasets[dataset_id] = {
                'filename': file.filename,
                'dataset_type': dataset_type,
                'parsed_data': parsed_data,
                'uploaded_at': None
            }
            
            # Persist to disk
            self._persist_dataset(dataset_id)
            
            return {
                'dataset_id': dataset_id,
                'filename': file.filename,
                'total_sessions': parsed_data['total_sessions'],
                'total_events': parsed_data['total_events'],
                'sessions': parsed_data['sessions'],
                'dataset_info': parsed_data.get('dataset_info', {})
            }
            
        except Exception as e:
            raise Exception(f"Failed to upload dataset: {str(e)}")
    
    async def start_annotation_job(
        self,
        dataset_id: str,
        llm_config: Dict[str, Any],
        dataset_name: str = "dataset",
        resume_job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start annotation job for uploaded dataset"""
        
        if dataset_id not in self.uploaded_datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Import SessionHandlingStrategy enum
        from app.services.llm_agents import SessionHandlingStrategy
        
        # Debug: Log received config
        print(f"[DEBUG] Received llm_config keys: {list(llm_config.keys())}")
        print(f"[DEBUG] custom_endpoints in config: {llm_config.get('custom_endpoints', 'NOT PRESENT')}")
        print(f"[DEBUG] analyst_model: {llm_config.get('analyst_model', 'NOT SET')}")
        
        # Create LLM config with all parameters
        config = LLMConfig(
            # Model selection
            analyst_model=llm_config.get('analyst_model', 'claude-3-5-sonnet-20241022'),
            critic_model=llm_config.get('critic_model', 'gpt-4o'),
            judge_model=llm_config.get('judge_model', 'gpt-4o'),
            
            # API keys
            anthropic_api_key=llm_config.get('anthropic_api_key'),
            openai_api_key=llm_config.get('openai_api_key'),
            google_api_key=llm_config.get('google_api_key'),
            ollama_base_url=llm_config.get('ollama_base_url', 'http://localhost:11434'),
            
            # Custom endpoints and fallback
            custom_endpoints=llm_config.get('custom_endpoints'),
            enable_fallback=llm_config.get('enable_fallback', False),
            fallback_analyst_model=llm_config.get('fallback_analyst_model', 'gpt-4o-mini'),
            fallback_critic_model=llm_config.get('fallback_critic_model', 'gpt-4o-mini'),
            fallback_judge_model=llm_config.get('fallback_judge_model', 'gpt-4o-mini'),
            fallback_retry_after=llm_config.get('fallback_retry_after', 5),
            
            # Session handling
            session_strategy=SessionHandlingStrategy(llm_config.get('session_strategy', 'truncate')),
            window_size=llm_config.get('window_size', 30),
            
            # Model parameters
            temperature=llm_config.get('temperature', 0.7),
            max_tokens_base=llm_config.get('max_tokens_base', 4096),
            max_tokens_cap=llm_config.get('max_tokens_cap', 16000),
            tokens_per_event=llm_config.get('tokens_per_event', 100),
            
            # Truncation limits
            truncate_content_small=llm_config.get('truncate_content_small', 200),
            truncate_content_medium=llm_config.get('truncate_content_medium', 150),
            truncate_content_large=llm_config.get('truncate_content_large', 100),
            truncate_reasoning_small=llm_config.get('truncate_reasoning_small', 300),
            truncate_reasoning_medium=llm_config.get('truncate_reasoning_medium', 200),
            truncate_reasoning_large=llm_config.get('truncate_reasoning_large', 150),
            
            # Custom prompts
            analyst_prompt_override=llm_config.get('analyst_prompt_override'),
            critic_prompt_override=llm_config.get('critic_prompt_override'),
            judge_prompt_override=llm_config.get('judge_prompt_override')
        )
        
        # Create orchestrator
        job_id = resume_job_id or str(uuid.uuid4())
        orchestrator = AnnotationOrchestrator(config)
        self.active_jobs[job_id] = orchestrator
        
        # Get sessions
        dataset = self.uploaded_datasets[dataset_id]
        sessions = dataset['parsed_data']['sessions']
        session_ids = [s['session_id'] for s in sessions]
        
        # Store session list for this job
        self.uploaded_datasets[dataset_id]['job_sessions'] = session_ids
        orchestrator.session_ids = session_ids  # Store in orchestrator for status retrieval
        
        # Start annotation in a background thread to avoid blocking the event loop
        def _run_annotation():
            asyncio.run(orchestrator.annotate_dataset(sessions, job_id, dataset_name))

        thread = threading.Thread(target=_run_annotation, daemon=True)
        thread.start()
        
        return {
            'job_id': job_id,
            'status': 'started',
            'total_sessions': len(sessions),
            'dataset_name': dataset_name,
            'session_ids': session_ids
        }
    
    async def get_dataset_info(self, dataset_id: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get dataset information with paginated session preview"""
        if dataset_id not in self.uploaded_datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        dataset = self.uploaded_datasets[dataset_id]
        parsed_data = dataset['parsed_data']
        sessions = parsed_data['sessions']
        
        # Calculate pagination
        total_sessions = len(sessions)
        start_idx = (page - 1) * limit
        end_idx = min(start_idx + limit, total_sessions)
        
        # Get paginated sessions (with limited events per session for preview)
        preview_sessions = []
        for session in sessions[start_idx:end_idx]:
            preview_session = {
                'session_id': session['session_id'],
                'num_events': session.get('num_events', len(session.get('events', []))),
                'start_time': session.get('start_time', ''),
                'end_time': session.get('end_time', ''),
                # Include only first 3 events for preview
                'events_preview': session.get('events', [])[:3]
            }
            preview_sessions.append(preview_session)
        
        return {
            'dataset_id': dataset_id,
            'filename': dataset['filename'],
            'total_sessions': total_sessions,
            'total_events': parsed_data.get('total_events', 0),
            'dataset_info': parsed_data.get('dataset_info', {}),
            'page': page,
            'limit': limit,
            'total_pages': (total_sessions + limit - 1) // limit,
            'sessions': preview_sessions
        }

    async def annotate_session(self, request: AnnotationRequest) -> Dict[str, Any]:
        """Annotate a single session"""
        # Create temporary config and orchestrator
        config = LLMConfig()
        orchestrator = AnnotationOrchestrator(config)
        
        session = {
            'session_id': request.session_id,
            'events': [event.dict() for event in request.events]
        }
        
        result = await orchestrator._annotate_session(session, "single_session")
        
        return {
            "session_id": request.session_id,
            "annotated_events": result['annotated_events'],
            "processing_time": 0.0,
            "flagged_for_review": result['flagged_for_review']
        }
    
    async def batch_annotate(self, request: BatchAnnotationRequest) -> str:
        """Submit batch annotation job"""
        # TODO: Implement batch annotation
        return "job_123"
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get batch job status (from active jobs or checkpoint)"""
        
        # Check active jobs first
        if job_id in self.active_jobs:
            orchestrator = self.active_jobs[job_id]
            progress = orchestrator.get_progress()
            
            status_response = {
                "job_id": job_id,
                "status": progress['status'],
                "total_sessions": progress['total_sessions'],
                "completed_sessions": progress['completed_sessions'],
                "current_session": progress['current_session'],
                "progress_percentage": (
                    progress['completed_sessions'] / progress['total_sessions'] * 100
                    if progress['total_sessions'] > 0 else 0
                ),
                "errors": progress['errors'],
                "stop_requested": progress.get('stop_requested', False),
                "session_ids": getattr(orchestrator, 'session_ids', []),
                "flagged_sessions": progress.get('flagged_sessions', []),
                "session_event_counts": getattr(orchestrator, 'session_event_counts', {}),
                # Diagnostics for disagreement model
                "disagreement_model": {
                    "loaded": getattr(orchestrator, 'similarity_model_loaded', False),
                    "error": getattr(orchestrator, 'similarity_model_error', None)
                }
            }
            
            return status_response
        
        # Check checkpoint file for completed/stopped jobs
        checkpoint_path = self.checkpoint_dir / f"{job_id}_checkpoint.json"
        if checkpoint_path.exists():
            try:
                with open(checkpoint_path, 'r') as f:
                    checkpoint = json.load(f)
                
                progress = checkpoint.get('progress', {})
                completed_sessions = checkpoint.get('completed_sessions', [])
                
                # Check if there's a summary file (job completed)
                job_dir = self.output_dir / job_id
                summary_files = list(job_dir.glob('*_summary.json')) if job_dir.exists() else []
                
                # Determine status
                if summary_files:
                    # Job completed, load summary for more info
                    with open(summary_files[0], 'r') as f:
                        summary = json.load(f)
                    status = 'completed'
                    total_sessions = summary.get('total_sessions', len(completed_sessions))
                    flagged_sessions = summary.get('flagged_sessions', progress.get('flagged_sessions', []))
                else:
                    # Job was stopped or is incomplete
                    status = progress.get('status', 'stopped')
                    total_sessions = progress.get('total_sessions', len(completed_sessions))
                    flagged_sessions = progress.get('flagged_sessions', [])
                
                status_response = {
                    "job_id": job_id,
                    "status": status,
                    "total_sessions": total_sessions,
                    "completed_sessions": len(completed_sessions),
                    "current_session": None,
                    "progress_percentage": (
                        len(completed_sessions) / total_sessions * 100
                        if total_sessions > 0 else 0
                    ),
                    "errors": progress.get('errors', []),
                    "stop_requested": False,
                    "session_ids": completed_sessions,
                    "flagged_sessions": flagged_sessions,
                    "session_event_counts": {},
                    "disagreement_model": {
                        "loaded": False,
                        "error": None
                    }
                }
                
                return status_response
            except Exception as e:
                print(f"[ERROR] Failed to load checkpoint for job {job_id}: {e}")
        
        raise ValueError(f"Job {job_id} not found")
    
    async def get_session_log(self, job_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed log for a specific session (from active job or saved logs)"""
        
        # Check active jobs first
        if job_id in self.active_jobs:
            orchestrator = self.active_jobs[job_id]
            return orchestrator.get_session_log(session_id, job_id)
        
        # Check saved log files for completed jobs
        job_dir = self.output_dir / job_id / "logs"
        log_file = job_dir / f"{session_id}_log.json"
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load log for session {session_id}: {e}")
        
        raise ValueError(f"Log for session {session_id} in job {job_id} not found")
    
    async def stop_job(self, job_id: str) -> Dict[str, Any]:
        """Request a job to stop gracefully"""
        if job_id not in self.active_jobs:
            raise ValueError(f"Job {job_id} not found")
        
        orchestrator = self.active_jobs[job_id]
        orchestrator.request_stop()
        
        return {
            "job_id": job_id,
            "status": "stop_requested",
            "message": "Stop request sent. The job will complete the current session and then stop."
        }
