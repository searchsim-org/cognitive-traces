"""
Export endpoints for annotated data
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from typing import Optional
from pathlib import Path
import json
import csv
import io

router = APIRouter()


@router.get("/csv")
async def export_csv(
    dataset: Optional[str] = None,
    session_ids: Optional[str] = Query(None, description="Comma-separated session IDs")
):
    """
    Export annotations as CSV file.
    Find the most recent cognitive traces CSV file for the dataset.
    """
    try:
        # Get project root (two levels up from app/api/endpoints/)
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        data_dir = project_root / "data"
        
        if not data_dir.exists():
            raise HTTPException(status_code=404, detail="Data directory not found")
        
        # Find the CSV file
        csv_file = None
        if dataset:
            # Look for the dataset-specific file
            csv_pattern = f"{dataset}_cognitive_traces.csv"
            # Search in all job directories
            for job_dir in data_dir.iterdir():
                if job_dir.is_dir() and not job_dir.name.startswith('.'):
                    candidate = job_dir / csv_pattern
                    if candidate.exists():
                        csv_file = candidate
                        break
        
        if not csv_file or not csv_file.exists():
            # Try to find any cognitive traces CSV
            for job_dir in data_dir.iterdir():
                if job_dir.is_dir() and not job_dir.name.startswith('.'):
                    for f in job_dir.glob("*_cognitive_traces.csv"):
                        csv_file = f
                        break
                    if csv_file:
                        break
        
        if not csv_file or not csv_file.exists():
            raise HTTPException(status_code=404, detail=f"CSV file not found for dataset: {dataset}")
        
        # Read and optionally filter by session IDs
        with open(csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if session_ids:
            # Filter by session IDs
            session_id_list = [sid.strip() for sid in session_ids.split(',')]
            lines = content.split('\n')
            header = lines[0] if lines else ''
            filtered_lines = [header]
            
            for line in lines[1:]:
                if line.strip() and any(line.startswith(f'"{sid}"') or line.startswith(sid) for sid in session_id_list):
                    filtered_lines.append(line)
            
            content = '\n'.join(filtered_lines)
        
        # Return as downloadable CSV
        filename = csv_file.name if not session_ids else f"{dataset}_filtered_cognitive_traces.csv"
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")


@router.get("/json")
async def export_json(
    dataset: Optional[str] = None,
    session_ids: Optional[str] = Query(None, description="Comma-separated session IDs")
):
    """
    Export annotations as JSON file.
    Converts CSV to structured JSON format.
    """
    try:
        # Get project root
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        data_dir = project_root / "data"
        
        if not data_dir.exists():
            raise HTTPException(status_code=404, detail="Data directory not found")
        
        # Find the CSV file (same logic as CSV export)
        csv_file = None
        if dataset:
            csv_pattern = f"{dataset}_cognitive_traces.csv"
            for job_dir in data_dir.iterdir():
                if job_dir.is_dir() and not job_dir.name.startswith('.'):
                    candidate = job_dir / csv_pattern
                    if candidate.exists():
                        csv_file = candidate
                        break
        
        if not csv_file or not csv_file.exists():
            for job_dir in data_dir.iterdir():
                if job_dir.is_dir() and not job_dir.name.startswith('.'):
                    for f in job_dir.glob("*_cognitive_traces.csv"):
                        csv_file = f
                        break
                    if csv_file:
                        break
        
        if not csv_file or not csv_file.exists():
            raise HTTPException(status_code=404, detail=f"CSV file not found for dataset: {dataset}")
        
        # Parse CSV to JSON
        sessions_data = {}
        with open(csv_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                session_id = row.get('session_id', '')
                
                # Filter by session IDs if provided
                if session_ids:
                    session_id_list = [sid.strip() for sid in session_ids.split(',')]
                    if session_id not in session_id_list:
                        continue
                
                if session_id not in sessions_data:
                    sessions_data[session_id] = {
                        'session_id': session_id,
                        'events': []
                    }
                
                sessions_data[session_id]['events'].append({
                    'event_id': row.get('event_id', ''),
                    'timestamp': row.get('event_timestamp', ''),
                    'action_type': row.get('action_type', ''),
                    'content': row.get('content', ''),
                    'cognitive_label': row.get('cognitive_label', ''),
                    'analyst_label': row.get('analyst_label', ''),
                    'analyst_justification': row.get('analyst_justification', ''),
                    'critic_label': row.get('critic_label', ''),
                    'critic_agreement': row.get('critic_agreement', ''),
                    'critic_justification': row.get('critic_justification', ''),
                    'judge_justification': row.get('judge_justification', ''),
                    'confidence_score': float(row.get('confidence_score', 0)),
                    'disagreement_score': float(row.get('disagreement_score', 0)),
                    'flagged_for_review': row.get('flagged_for_review', '').lower() == 'true',
                    'user_override': row.get('user_override', '').lower() == 'true',
                    'override_version': int(row.get('override_version', 1)),
                    'override_timestamp': row.get('override_timestamp', '')
                })
        
        # Convert to list
        result = {
            'dataset': dataset or 'unknown',
            'total_sessions': len(sessions_data),
            'sessions': list(sessions_data.values())
        }
        
        # Return as downloadable JSON
        filename = f"{dataset}_cognitive_traces.json" if dataset else "cognitive_traces.json"
        json_content = json.dumps(result, indent=2)
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting JSON: {str(e)}")

