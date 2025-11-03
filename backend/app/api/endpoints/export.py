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
    Export summary report as JSON file.
    Returns the summary.json file with job metadata and statistics.
    """
    try:
        # Get project root
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        data_dir = project_root / "data"
        
        if not data_dir.exists():
            raise HTTPException(status_code=404, detail="Data directory not found")
        
        # Find the summary JSON file
        summary_file = None
        if dataset:
            summary_pattern = f"{dataset}_summary.json"
            for job_dir in data_dir.iterdir():
                if job_dir.is_dir() and not job_dir.name.startswith('.'):
                    candidate = job_dir / summary_pattern
                    if candidate.exists():
                        summary_file = candidate
                        break
        
        if not summary_file or not summary_file.exists():
            # Try to find any summary JSON
            for job_dir in data_dir.iterdir():
                if job_dir.is_dir() and not job_dir.name.startswith('.'):
                    for f in job_dir.glob("*_summary.json"):
                        summary_file = f
                        break
                    if summary_file:
                        break
        
        if not summary_file or not summary_file.exists():
            raise HTTPException(status_code=404, detail=f"Summary JSON file not found for dataset: {dataset}")
        
        # Read the summary file
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Optionally filter by session IDs if needed
        if session_ids:
            session_id_list = [sid.strip() for sid in session_ids.split(',')]
            # Filter flagged_sessions if present
            if 'flagged_sessions' in summary_data:
                summary_data['flagged_sessions'] = [
                    sid for sid in summary_data['flagged_sessions'] 
                    if sid in session_id_list
                ]
        
        # Return as downloadable JSON
        filename = f"{dataset}_summary.json" if dataset else "summary.json"
        json_content = json.dumps(summary_data, indent=2)
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting JSON: {str(e)}")

