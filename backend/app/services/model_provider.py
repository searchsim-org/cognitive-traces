"""
Service for managing LLM model providers and retrieving available models
"""

import anthropic
import openai
from typing import List, Dict, Any, Optional
import httpx
import os


class ModelProvider:
    """Manage different LLM providers and their models"""
    
    # Define cost-efficient models for each provider
    EFFICIENT_MODELS = {
        'anthropic': [
            'claude-3-5-sonnet-20241022',
            'claude-3-5-haiku-20241022',
            'claude-3-haiku-20240307',
            'claude-3-sonnet-20240229',
        ],
        'openai': [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-4-turbo-preview',
            'gpt-3.5-turbo',
        ],
        'google': [
            'gemini-1.5-flash',
            'gemini-1.5-flash-8b',
            'gemini-1.5-pro',
            'gemini-2.0-flash-exp',
        ],
    }
    
    @staticmethod
    async def get_anthropic_models(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available Anthropic models"""
        try:
            # Anthropic doesn't have a models endpoint, so we return our curated list
            models = [
                {
                    'id': 'claude-3-5-sonnet-20241022',
                    'name': 'Claude 3.5 Sonnet',
                    'provider': 'anthropic',
                    'description': 'Most intelligent model, best for complex reasoning',
                    'context_window': 200000,
                    'cost': 'medium',
                    'recommended': True
                },
                {
                    'id': 'claude-3-5-haiku-20241022',
                    'name': 'Claude 3.5 Haiku',
                    'provider': 'anthropic',
                    'description': 'Fastest and most compact model, great for quick tasks',
                    'context_window': 200000,
                    'cost': 'low',
                    'recommended': True
                },
                {
                    'id': 'claude-3-haiku-20240307',
                    'name': 'Claude 3 Haiku',
                    'provider': 'anthropic',
                    'description': 'Fast and affordable',
                    'context_window': 200000,
                    'cost': 'low',
                    'recommended': False
                },
                {
                    'id': 'claude-3-sonnet-20240229',
                    'name': 'Claude 3 Sonnet',
                    'provider': 'anthropic',
                    'description': 'Balanced performance and speed',
                    'context_window': 200000,
                    'cost': 'medium',
                    'recommended': False
                },
                {
                    'id': 'claude-3-opus-20240229',
                    'name': 'Claude 3 Opus',
                    'provider': 'anthropic',
                    'description': 'Most powerful for highly complex tasks',
                    'context_window': 200000,
                    'cost': 'high',
                    'recommended': False
                },
            ]
            return models
        except Exception as e:
            print(f"Error fetching Anthropic models: {e}")
            return []
    
    @staticmethod
    async def get_openai_models(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available OpenAI models"""
        try:
            # If API key provided, fetch from API
            if api_key:
                client = openai.OpenAI(api_key=api_key)
                models_response = client.models.list()
                all_models = [m.id for m in models_response.data]
                
                # Filter to only chat models we care about
                filtered = [m for m in all_models if any(
                    efficient in m for efficient in ModelProvider.EFFICIENT_MODELS['openai']
                )]
            else:
                # Return curated list without API call
                filtered = ModelProvider.EFFICIENT_MODELS['openai']
            
            # Format with metadata
            models = []
            model_metadata = {
                'gpt-4o': {
                    'name': 'GPT-4o',
                    'description': 'High intelligence, multimodal flagship model',
                    'context_window': 128000,
                    'cost': 'medium',
                    'recommended': True
                },
                'gpt-4o-mini': {
                    'name': 'GPT-4o Mini',
                    'description': 'Affordable and intelligent small model',
                    'context_window': 128000,
                    'cost': 'low',
                    'recommended': True
                },
                'gpt-4-turbo': {
                    'name': 'GPT-4 Turbo',
                    'description': 'Latest GPT-4 Turbo with vision',
                    'context_window': 128000,
                    'cost': 'medium',
                    'recommended': True
                },
                'gpt-4-turbo-preview': {
                    'name': 'GPT-4 Turbo Preview',
                    'description': 'Preview of GPT-4 Turbo',
                    'context_window': 128000,
                    'cost': 'medium',
                    'recommended': False
                },
                'gpt-3.5-turbo': {
                    'name': 'GPT-3.5 Turbo',
                    'description': 'Fast and efficient',
                    'context_window': 16385,
                    'cost': 'very-low',
                    'recommended': True
                },
            }
            
            for model_id in filtered:
                base_id = model_id.split('-20')[0] if '-20' in model_id else model_id
                metadata = model_metadata.get(base_id, {
                    'name': model_id,
                    'description': 'OpenAI model',
                    'context_window': 8192,
                    'cost': 'unknown',
                    'recommended': False
                })
                
                models.append({
                    'id': model_id,
                    'provider': 'openai',
                    **metadata
                })
            
            return models
            
        except Exception as e:
            print(f"Error fetching OpenAI models: {e}")
            # Return default list on error
            return [
                {
                    'id': 'gpt-4o',
                    'name': 'GPT-4o',
                    'provider': 'openai',
                    'description': 'High intelligence flagship',
                    'context_window': 128000,
                    'cost': 'medium',
                    'recommended': True
                },
                {
                    'id': 'gpt-4o-mini',
                    'name': 'GPT-4o Mini',
                    'provider': 'openai',
                    'description': 'Affordable and intelligent',
                    'context_window': 128000,
                    'cost': 'low',
                    'recommended': True
                },
            ]
    
    @staticmethod
    async def get_google_models(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available Google Gemini models"""
        try:
            # Google's Generative AI API
            models = [
                {
                    'id': 'gemini-2.0-flash-exp',
                    'name': 'Gemini 2.0 Flash',
                    'provider': 'google',
                    'description': 'Latest experimental model, extremely fast',
                    'context_window': 1000000,
                    'cost': 'low',
                    'recommended': True
                },
                {
                    'id': 'gemini-1.5-flash',
                    'name': 'Gemini 1.5 Flash',
                    'provider': 'google',
                    'description': 'Fast and versatile performance',
                    'context_window': 1000000,
                    'cost': 'low',
                    'recommended': True
                },
                {
                    'id': 'gemini-1.5-flash-8b',
                    'name': 'Gemini 1.5 Flash-8B',
                    'provider': 'google',
                    'description': 'Smaller, faster, and cheaper',
                    'context_window': 1000000,
                    'cost': 'very-low',
                    'recommended': True
                },
                {
                    'id': 'gemini-1.5-pro',
                    'name': 'Gemini 1.5 Pro',
                    'provider': 'google',
                    'description': 'Most capable model for complex tasks',
                    'context_window': 2000000,
                    'cost': 'medium',
                    'recommended': True
                },
            ]
            return models
            
        except Exception as e:
            print(f"Error fetching Google models: {e}")
            return []
    
    @staticmethod
    async def get_ollama_models(base_url: str = "http://localhost:11434") -> List[Dict[str, Any]]:
        """Get available Ollama models from local instance"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    
                    for model in data.get('models', []):
                        model_name = model.get('name', '')
                        
                        models.append({
                            'id': model_name,
                            'name': model_name.split(':')[0].title(),
                            'provider': 'ollama',
                            'description': f"Local Ollama model - {model.get('size', 'unknown size')}",
                            'context_window': model.get('context_length', 8192),
                            'cost': 'free',
                            'recommended': True,
                            'size': model.get('size'),
                            'modified': model.get('modified_at')
                        })
                    
                    return models
                else:
                    return []
                    
        except httpx.ConnectError:
            print(f"Ollama not reachable at {base_url}. Make sure Ollama is running.")
            return []
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
            return []
    
    @staticmethod
    async def get_all_models(
        anthropic_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        google_key: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        include_ollama: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available models from all providers"""
        
        models = {
            'anthropic': await ModelProvider.get_anthropic_models(anthropic_key),
            'openai': await ModelProvider.get_openai_models(openai_key),
            'google': await ModelProvider.get_google_models(google_key),
        }
        
        if include_ollama:
            models['ollama'] = await ModelProvider.get_ollama_models(ollama_url)
        
        return models
    
    @staticmethod
    def get_recommended_models() -> Dict[str, str]:
        """Get recommended models for each agent"""
        return {
            'analyst': 'claude-3-5-sonnet-20241022',
            'critic': 'gpt-4o',
            'judge': 'gpt-4o',
        }

