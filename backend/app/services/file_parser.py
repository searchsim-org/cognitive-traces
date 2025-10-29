"""
File parsing service for extracting sessions from uploaded datasets
"""

import csv
import json
import io
from typing import List, Dict, Any
from collections import defaultdict
import pandas as pd


class FileParser:
    """Parse uploaded CSV/JSON files and extract sessions"""
    
    @staticmethod
    async def parse_file(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse uploaded file and extract sessions
        
        Args:
            file_content: Raw file bytes
            filename: Name of uploaded file
            
        Returns:
            Dict with sessions and metadata
        """
        if filename.endswith('.csv'):
            return await FileParser._parse_csv(file_content)
        elif filename.endswith('.json'):
            return await FileParser._parse_json(file_content)
        else:
            raise ValueError(f"Unsupported file format: {filename}")
    
    @staticmethod
    async def _parse_csv(file_content: bytes) -> Dict[str, Any]:
        """Parse CSV file and extract sessions"""
        try:
            # Read CSV into pandas DataFrame
            df = pd.read_csv(io.BytesIO(file_content))
            
            # Validate required columns
            required_cols = ['session_id', 'timestamp', 'action_type', 'content']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
            
            # Group events by session_id
            sessions_dict = defaultdict(list)
            
            for _, row in df.iterrows():
                event = {
                    'event_id': str(row.get('event_id', f"{row['session_id']}_{row['timestamp']}")),
                    'timestamp': str(row['timestamp']),
                    'action_type': str(row['action_type']),
                    'content': str(row['content']),
                    'metadata': {}
                }
                
                # Add any additional columns as metadata
                for col in df.columns:
                    if col not in required_cols and col != 'event_id':
                        event['metadata'][col] = row[col]
                
                sessions_dict[str(row['session_id'])].append(event)
            
            # Convert to list of sessions
            sessions = []
            for session_id, events in sessions_dict.items():
                # Sort events by timestamp
                events.sort(key=lambda e: e['timestamp'])
                
                sessions.append({
                    'session_id': session_id,
                    'num_events': len(events),
                    'start_time': events[0]['timestamp'],
                    'end_time': events[-1]['timestamp'],
                    'events': events
                })
            
            return {
                'total_sessions': len(sessions),
                'total_events': len(df),
                'sessions': sessions,
                'dataset_info': {
                    'columns': list(df.columns),
                    'action_types': df['action_type'].unique().tolist()
                }
            }
            
        except Exception as e:
            raise ValueError(f"Error parsing CSV file: {str(e)}")
    
    @staticmethod
    async def _parse_json(file_content: bytes) -> Dict[str, Any]:
        """Parse JSON file and extract sessions"""
        try:
            data = json.loads(file_content.decode('utf-8'))
            
            # Handle different JSON structures
            if isinstance(data, list):
                # List of events - group by session_id
                sessions_dict = defaultdict(list)
                
                for event in data:
                    if 'session_id' not in event:
                        raise ValueError("Each event must have a 'session_id' field")
                    
                    sessions_dict[str(event['session_id'])].append(event)
                
                sessions = []
                total_events = 0
                
                for session_id, events in sessions_dict.items():
                    events.sort(key=lambda e: e.get('timestamp', ''))
                    sessions.append({
                        'session_id': session_id,
                        'num_events': len(events),
                        'start_time': events[0].get('timestamp', ''),
                        'end_time': events[-1].get('timestamp', ''),
                        'events': events
                    })
                    total_events += len(events)
                
                return {
                    'total_sessions': len(sessions),
                    'total_events': total_events,
                    'sessions': sessions
                }
                
            elif isinstance(data, dict) and 'sessions' in data:
                # Already structured as sessions
                sessions = data['sessions']
                total_events = sum(s.get('num_events', len(s.get('events', []))) for s in sessions)
                
                return {
                    'total_sessions': len(sessions),
                    'total_events': total_events,
                    'sessions': sessions
                }
            else:
                raise ValueError("JSON must be a list of events or dict with 'sessions' key")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing JSON file: {str(e)}")

