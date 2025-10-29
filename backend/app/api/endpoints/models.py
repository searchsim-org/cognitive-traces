"""
Model management endpoints
"""

from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
from app.services.model_provider import ModelProvider

router = APIRouter()


@router.get("/available")
async def get_available_models(
    anthropic_key: Optional[str] = Query(None, description="Anthropic API key for validation"),
    openai_key: Optional[str] = Query(None, description="OpenAI API key for validation"),
    google_key: Optional[str] = Query(None, description="Google API key for validation"),
    ollama_url: Optional[str] = Query("http://localhost:11434", description="Ollama base URL"),
    include_ollama: bool = Query(True, description="Include Ollama models")
) -> Dict[str, Any]:
    """
    Get all available models from all providers.
    Only returns cost-efficient models suitable for cognitive annotation tasks.
    """
    models = await ModelProvider.get_all_models(
        anthropic_key=anthropic_key,
        openai_key=openai_key,
        google_key=google_key,
        ollama_url=ollama_url,
        include_ollama=include_ollama
    )
    
    return {
        'models': models,
        'recommended': ModelProvider.get_recommended_models(),
        'total_count': sum(len(provider_models) for provider_models in models.values())
    }


@router.get("/anthropic")
async def get_anthropic_models(
    api_key: Optional[str] = Query(None, description="Anthropic API key")
):
    """Get available Anthropic Claude models"""
    models = await ModelProvider.get_anthropic_models(api_key)
    return {'models': models, 'count': len(models)}


@router.get("/openai")
async def get_openai_models(
    api_key: Optional[str] = Query(None, description="OpenAI API key")
):
    """Get available OpenAI GPT models"""
    models = await ModelProvider.get_openai_models(api_key)
    return {'models': models, 'count': len(models)}


@router.get("/google")
async def get_google_models(
    api_key: Optional[str] = Query(None, description="Google API key")
):
    """Get available Google Gemini models"""
    models = await ModelProvider.get_google_models(api_key)
    return {'models': models, 'count': len(models)}


@router.get("/ollama")
async def get_ollama_models(
    base_url: str = Query("http://localhost:11434", description="Ollama base URL")
):
    """Get available local Ollama models"""
    models = await ModelProvider.get_ollama_models(base_url)
    return {
        'models': models,
        'count': len(models),
        'ollama_url': base_url,
        'connected': len(models) > 0
    }


@router.get("/info")
async def get_model_info():
    """Get information about model providers and recommendations"""
    return {
        'providers': {
            'anthropic': {
                'name': 'Anthropic',
                'description': 'Claude models - excellent reasoning and analysis',
                'api_key_url': 'https://console.anthropic.com/',
                'recommended_for': ['analyst', 'complex reasoning']
            },
            'openai': {
                'name': 'OpenAI',
                'description': 'GPT models - versatile and powerful',
                'api_key_url': 'https://platform.openai.com/api-keys',
                'recommended_for': ['critic', 'judge', 'general tasks']
            },
            'google': {
                'name': 'Google',
                'description': 'Gemini models - fast with large context windows',
                'api_key_url': 'https://makersuite.google.com/app/apikey',
                'recommended_for': ['fast processing', 'large contexts']
            },
            'ollama': {
                'name': 'Ollama',
                'description': 'Local models - free, private, no API keys needed',
                'setup_url': 'https://ollama.ai/',
                'recommended_for': ['privacy', 'offline use', 'cost-free']
            }
        },
        'recommended_config': ModelProvider.get_recommended_models(),
        'cost_tiers': {
            'very-low': 'Best for high-volume, simple tasks',
            'low': 'Good balance of cost and performance',
            'medium': 'High quality for complex reasoning',
            'high': 'Maximum capability for critical tasks',
            'free': 'Local Ollama models (requires local setup)'
        }
    }
