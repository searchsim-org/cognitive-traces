"""
Annotation orchestrator with progress tracking, checkpoints, and incremental writing
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.llm_agents import AnalystAgent, CriticAgent, JudgeAgent, LLMConfig


class AnnotationOrchestrator:
    """Orchestrates the multi-agent annotation process with progress tracking"""
    
    def __init__(
        self,
        config: LLMConfig,
        output_dir: str = "data",
        checkpoint_dir: str = "data/checkpoints"
    ):
        self.config = config
        
        # Get project root (one level up from backend directory)
        backend_dir = Path(__file__).resolve().parent.parent.parent  # Goes up to backend/
        project_root = backend_dir.parent  # Goes up to project root
        
        # Use absolute paths from project root
        self.output_dir = (project_root / output_dir).resolve()
        self.checkpoint_dir = (project_root / checkpoint_dir).resolve()
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[INFO] Project root: {project_root}")
        print(f"[INFO] Data output directory: {self.output_dir}")
        
        # Initialize agents
        self.analyst = AnalystAgent(config)
        self.critic = CriticAgent(config)
        self.judge = JudgeAgent(config)
        
        # For semantic similarity comparison
        self.similarity_model = None
        self.similarity_model_loaded: bool = False
        self.similarity_model_error: Optional[str] = None
        
        # Progress tracking
        self.progress = {
            'total_sessions': 0,
            'completed_sessions': 0,
            'current_session': None,
            'status': 'idle',
            'errors': [],
            'stop_requested': False,
            'flagged_sessions': []
        }
        
        # Session logs
        self.session_logs = {}
        # Session event counts (session_id -> number of events)
        self.session_event_counts = {}
    
    async def annotate_dataset(
        self,
        sessions: List[Dict[str, Any]],
        job_id: str,
        dataset_name: str = "dataset"
    ) -> Dict[str, Any]:
        """
        Annotate entire dataset with progress tracking and checkpointing
        
        Args:
            sessions: List of sessions to annotate
            job_id: Unique job identifier
            dataset_name: Name for output files
            
        Returns:
            Job completion status and output file path
        """
        self.progress['total_sessions'] = len(sessions)
        self.progress['status'] = 'processing'
        
        # Check for existing checkpoint
        checkpoint_path = self.checkpoint_dir / f"{job_id}_checkpoint.json"
        completed_session_ids = set()
        
        if checkpoint_path.exists():
            checkpoint = self._load_checkpoint(checkpoint_path)
            completed_session_ids = set(checkpoint.get('completed_sessions', []))
            self.progress['completed_sessions'] = len(completed_session_ids)
        
        # Create job-specific directory
        job_dir = self.output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory for this job
        logs_dir = job_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Output file for incremental writing
        output_file = job_dir / f"{dataset_name}_cognitive_traces.csv"
        
        # Write CSV header if file doesn't exist
        if not output_file.exists():
            self._write_csv_header(output_file)
        
        print(f"[INFO] Output directory: {job_dir}")
        print(f"[INFO] Output file: {output_file}")
        print(f"[INFO] Logs directory: {logs_dir}")
        
        # Process each session
        flagged_sessions = []
        
        for session in sessions:
            # Check if stop was requested
            if self.progress['stop_requested']:
                print(f"[INFO] Stop requested. Stopping annotation job {job_id}")
                self.progress['status'] = 'stopped'
                self.progress['current_session'] = None
                break
            
            session_id = session['session_id']
            
            # Skip if already completed
            if session_id in completed_session_ids:
                continue
            
            try:
                self.progress['current_session'] = session_id
                self.progress['status'] = f'processing {session_id}'
                
                # Record event count for UI
                try:
                    self.session_event_counts[session_id] = len(session.get('events', []))
                except Exception:
                    self.session_event_counts[session_id] = 0

                # Annotate session
                result = await self._annotate_session(session, job_id, logs_dir)
                
                # Write results incrementally
                self._append_to_csv(output_file, result)
                
                # Check for disagreements
                if result.get('flagged_for_review'):
                    flagged_sessions.append(session_id)
                    if session_id not in self.progress['flagged_sessions']:
                        self.progress['flagged_sessions'].append(session_id)
                
                # Update progress
                self.progress['completed_sessions'] += 1
                completed_session_ids.add(session_id)
                
                # Save checkpoint
                self._save_checkpoint(
                    checkpoint_path,
                    completed_session_ids,
                    self.progress
                )
                
            except Exception as e:
                error_msg = f"Error processing session {session_id}: {str(e)}"
                self.progress['errors'].append(error_msg)
                print(f"[ERROR] {error_msg}")
                continue
        
        # Final status
        if not self.progress['stop_requested']:
            self.progress['status'] = 'completed'
        self.progress['current_session'] = None
        
        # Create summary file
        summary = {
            'job_id': job_id,
            'dataset_name': dataset_name,
            'total_sessions': self.progress['total_sessions'],
            'completed_sessions': self.progress['completed_sessions'],
            'remaining_sessions': self.progress['total_sessions'] - self.progress['completed_sessions'],
            'flagged_sessions': flagged_sessions,
            'errors': self.progress['errors'],
            'output_file': str(output_file),
            'status': self.progress['status'],
            'stopped': self.progress['status'] == 'stopped',
            'checkpoint_file': str(checkpoint_path) if checkpoint_path.exists() else None,
            'completed_at': datetime.now().isoformat()
        }
        
        summary_file = job_dir / f"{dataset_name}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"[INFO] Summary saved to: {summary_file}")
        
        return summary
    
    async def _annotate_session(
        self,
        session: Dict[str, Any],
        job_id: str,
        logs_dir: Path
    ) -> Dict[str, Any]:
        """Annotate a single session using multi-agent framework"""
        
        session_id = session['session_id']
        events = session['events']
        
        # Initialize session log
        log = {
            'session_id': session_id,
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'events': [],
            'agent_interactions': []
        }
        
        try:
            # Step 1: Analyst analyzes
            log['agent_interactions'].append({
                'step': 1,
                'agent': 'analyst',
                'status': 'started'
            })
            
            analyst_result = await self.analyst.analyze(events)
            
            log['agent_interactions'][-1].update({
                'status': 'completed',
                'elapsed_time': analyst_result['elapsed_time'],
                'decisions': analyst_result['decisions']
            })
            
            # Step 2: Critic reviews
            log['agent_interactions'].append({
                'step': 2,
                'agent': 'critic',
                'status': 'started'
            })
            
            critic_result = await self.critic.review(events, analyst_result['decisions'])
            
            log['agent_interactions'][-1].update({
                'status': 'completed',
                'elapsed_time': critic_result['elapsed_time'],
                'decisions': critic_result['decisions']
            })
            
            # Calculate disagreement scores
            disagreement_scores = self._calculate_disagreement(
                analyst_result['decisions'],
                critic_result['decisions']
            )
            
            # Step 3: Judge decides
            log['agent_interactions'].append({
                'step': 3,
                'agent': 'judge',
                'status': 'started'
            })
            
            judge_result = await self.judge.decide(
                events,
                analyst_result['decisions'],
                critic_result['decisions']
            )
            
            log['agent_interactions'][-1].update({
                'status': 'completed',
                'elapsed_time': judge_result['elapsed_time'],
                'decisions': judge_result['decisions']
            })
            
            # Determine if session should be flagged for review
            max_disagreement = max(disagreement_scores) if disagreement_scores else 0
            flagged_for_review = max_disagreement > 0.75  # Top 25% - adjust threshold as needed
            
            # Build annotated events (guard against length mismatches)
            annotated_events = []
            analyst_decisions = analyst_result.get('decisions', [])
            critic_decisions = critic_result.get('decisions', [])
            judge_decisions = judge_result.get('decisions', [])

            for i, event in enumerate(events):
                has_analyst = i < len(analyst_decisions)
                has_critic = i < len(critic_decisions)
                has_judge = i < len(judge_decisions)
                annotated_event = {
                    'session_id': session_id,
                    'event_id': event['event_id'],
                    'timestamp': event['timestamp'],
                    'action_type': event['action_type'],
                    'content': event['content'],
                    'cognitive_label': judge_decisions[i]['final_label'] if has_judge else (critic_decisions[i]['label'] if has_critic else (analyst_decisions[i]['label'] if has_analyst else 'Unknown')),
                    'analyst_label': analyst_decisions[i]['label'] if has_analyst else 'Unknown',
                    'analyst_justification': analyst_decisions[i].get('justification', '') if has_analyst else '',
                    'critic_label': critic_decisions[i]['label'] if has_critic else 'Unknown',
                    'critic_agreement': critic_decisions[i].get('agreement', 0) if has_critic else 0,
                    'critic_justification': critic_decisions[i].get('justification', '') if has_critic else '',
                    'judge_justification': judge_decisions[i].get('justification', '') if has_judge else '',
                    'confidence_score': judge_decisions[i].get('confidence', 0.0) if has_judge else 0.0,
                    'disagreement_score': disagreement_scores[i] if i < len(disagreement_scores) else 0,
                    'flagged_for_review': (disagreement_scores[i] > 0.75) if i < len(disagreement_scores) else False,
                    # Versioning fields for non-destructive overrides
                    'user_override': False,
                    'override_version': 1,
                    'override_timestamp': datetime.now().isoformat()
                }
                annotated_events.append(annotated_event)
            
            log['events'] = annotated_events
            log['flagged_for_review'] = flagged_for_review
            log['max_disagreement'] = max_disagreement
            
            # Save log
            self.session_logs[session_id] = log
            log_file = logs_dir / f"{session_id}_log.json"
            with open(log_file, 'w') as f:
                json.dump(log, f, indent=2)
            
            print(f"[INFO] Saved log to: {log_file}")
            
            return {
                'session_id': session_id,
                'annotated_events': annotated_events,
                'flagged_for_review': flagged_for_review,
                'log': log
            }
            
        except Exception as e:
            log['error'] = str(e)
            log['status'] = 'failed'
            raise
    
    def _calculate_disagreement(
        self,
        analyst_decisions: List[Dict[str, Any]],
        critic_decisions: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Calculate semantic disagreement between Analyst and Critic
        
        Uses sentence embedding similarity between justifications
        Returns disagreement score (0-1, higher = more disagreement)
        """
        try:
            # Lazy load similarity model
            if self.similarity_model is None:
                try:
                    print("[DISAGREEMENT] Loading SentenceTransformer 'all-MiniLM-L6-v2'...")
                    self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.similarity_model_loaded = True
                    self.similarity_model_error = None
                    print("[DISAGREEMENT] SentenceTransformer loaded successfully.")
                except Exception as load_err:
                    self.similarity_model = None
                    self.similarity_model_loaded = False
                    self.similarity_model_error = str(load_err)
                    print(f"[DISAGREEMENT][ERROR] Failed to load SentenceTransformer: {load_err}")
                    # Early return zeros so pipeline continues without flags
                    return [0.0] * len(analyst_decisions)
            
            disagreement_scores = []
            
            for analyst, critic in zip(analyst_decisions, critic_decisions):
                # Label disagreement
                label_disagree = 1.0 if analyst['label'] != critic['label'] else 0.0
                
                # Semantic disagreement in justifications
                analyst_text = analyst['justification']
                critic_text = critic['justification']
                
                embeddings = self.similarity_model.encode([analyst_text, critic_text])
                similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                semantic_disagree = 1.0 - similarity  # Convert similarity to disagreement
                
                # Combined score (weighted)
                total_disagreement = 0.6 * label_disagree + 0.4 * semantic_disagree
                disagreement_scores.append(float(total_disagreement))
            
            return disagreement_scores
            
        except Exception as e:
            print(f"[DISAGREEMENT][ERROR] Error calculating disagreement: {e}")
            return [0.0] * len(analyst_decisions)
    
    def _write_csv_header(self, output_file: Path):
        """Write CSV header"""
        header = [
            'session_id', 'event_id', 'event_timestamp', 'action_type', 'content',
            'cognitive_label', 'analyst_label', 'analyst_justification',
            'critic_label', 'critic_agreement', 'critic_justification',
            'judge_justification', 'confidence_score', 'disagreement_score',
            'flagged_for_review',
            # New versioning/audit columns
            'user_override', 'override_version', 'override_timestamp'
        ]
        
        with open(output_file, 'w') as f:
            f.write(','.join(header) + '\n')
    
    def _append_to_csv(self, output_file: Path, result: Dict[str, Any]):
        """Append annotated events to CSV file"""
        import csv
        
        with open(output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            
            for event in result['annotated_events']:
                row = [
                    event['session_id'],
                    event['event_id'],
                    event['timestamp'],
                    event['action_type'],
                    event['content'][:500],  # Truncate long content
                    event['cognitive_label'],
                    event['analyst_label'],
                    event['analyst_justification'][:500],
                    event['critic_label'],
                    event['critic_agreement'],
                    event['critic_justification'][:500],
                    event['judge_justification'][:500],
                    event['confidence_score'],
                    event['disagreement_score'],
                    event.get('flagged_for_review', False),
                    # New versioning/audit columns (with safe defaults)
                    event.get('user_override', False),
                    event.get('override_version', 1),
                    event.get('override_timestamp', datetime.now().isoformat())
                ]
                writer.writerow(row)
    
    def _save_checkpoint(
        self,
        checkpoint_path: Path,
        completed_sessions: set,
        progress: Dict[str, Any]
    ):
        """Save checkpoint for recovery"""
        checkpoint = {
            'completed_sessions': list(completed_sessions),
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def _load_checkpoint(self, checkpoint_path: Path) -> Dict[str, Any]:
        """Load checkpoint"""
        with open(checkpoint_path, 'r') as f:
            return json.load(f)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress"""
        return self.progress.copy()
    
    def get_session_log(self, session_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Get log for specific session"""
        # First check in-memory logs
        if session_id in self.session_logs:
            return self.session_logs[session_id]
        
        # Try to load from file if not in memory
        # New structure: data/{job_id}/logs/{session_id}_log.json
        log_file = self.output_dir / job_id / "logs" / f"{session_id}_log.json"
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    log = json.load(f)
                    self.session_logs[session_id] = log  # Cache it
                    return log
            except Exception as e:
                print(f"Error loading log file {log_file}: {e}")
                return None
        
        print(f"[WARN] Log file not found: {log_file}")
        return None
    
    def request_stop(self):
        """Request the annotation job to stop gracefully"""
        self.progress['stop_requested'] = True
        print(f"[INFO] Stop requested for annotation job")
    
    def is_stopped(self) -> bool:
        """Check if the job was stopped"""
        return self.progress['status'] == 'stopped'

