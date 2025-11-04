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
    mistral_key: Optional[str] = Query(None, description="Mistral API key for validation"),
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
        mistral_key=mistral_key,
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


@router.get("/mistral")
async def get_mistral_models(
    api_key: Optional[str] = Query(None, description="Mistral API key")
):
    """Get available Mistral AI models"""
    models = await ModelProvider.get_mistral_models(api_key)
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


@router.post("/custom/test")
async def test_custom_endpoint(
    base_url: str = Query(..., description="Custom endpoint base URL"),
    api_key: Optional[str] = Query(None, description="API key if required")
):
    """
    Test custom OpenAI-compatible endpoint and discover available models.
    Acts as a proxy to avoid CORS issues.
    """
    import httpx
    
    # Normalize base URL
    base_url = base_url.rstrip('/')
    
    # Add /v1 if not present
    if not base_url.endswith('/v1'):
        if '/v1/' in base_url:
            # Already has /v1 in path, just normalize
            pass
        else:
            base_url = f"{base_url}/v1"
    
    models_url = f"{base_url}/models"
    
    try:
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(models_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            models_list = data.get('data', data.get('models', []))
            
            # Convert to our format
            models = [
                {
                    'id': model.get('id', model.get('model', 'unknown')),
                    'name': model.get('id', model.get('model', 'unknown')),
                    'provider': 'custom',
                    'description': model.get('description', 'Custom model'),
                    'contextWindow': model.get('context_length', 8192)
                }
                for model in models_list
            ]
            
            return {
                'success': True,
                'models': models,
                'count': len(models),
                'base_url': base_url.replace('/v1', '')  # Return without /v1
            }
            
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"HTTP {e.response.status_code}: {e.response.text}"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to endpoint. Check the URL and ensure it's accessible."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Connection timed out. The endpoint may be slow or unreachable."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect: {str(e)}"
        )


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
            'mistral': {
                'name': 'Mistral AI',
                'description': 'European models with strong performance',
                'api_key_url': 'https://console.mistral.ai/',
                'recommended_for': ['balanced performance', 'European data privacy']
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
