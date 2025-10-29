"""
Service for handling annotation operations
"""

import uuid
import asyncio
import threading
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
        
        # Create LLM config
        config = LLMConfig(
            analyst_model=llm_config.get('analyst_model', 'claude-3-5-sonnet-20241022'),
            critic_model=llm_config.get('critic_model', 'gpt-4o'),
            judge_model=llm_config.get('judge_model', 'gpt-4o'),
            anthropic_api_key=llm_config.get('anthropic_api_key'),
            openai_api_key=llm_config.get('openai_api_key'),
            google_api_key=llm_config.get('google_api_key'),
            ollama_base_url=llm_config.get('ollama_base_url', 'http://localhost:11434')
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
        """Get batch job status"""
        if job_id not in self.active_jobs:
            raise ValueError(f"Job {job_id} not found")
        
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
            "session_event_counts": getattr(orchestrator, 'session_event_counts', {})
        }
        
        return status_response
    
    async def get_session_log(self, job_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed log for a specific session"""
        if job_id not in self.active_jobs:
            raise ValueError(f"Job {job_id} not found")
        
        orchestrator = self.active_jobs[job_id]
        return orchestrator.get_session_log(session_id, job_id)
    
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
