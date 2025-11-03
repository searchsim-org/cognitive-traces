"""
LLM Agent implementations for cognitive trace annotation
"""

import anthropic
import openai
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import time
import asyncio
import httpx
import google.generativeai as genai


class ModelProvider(str, Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    OLLAMA = "ollama"


class SessionHandlingStrategy(str, Enum):
    """Strategy for handling long sessions"""
    TRUNCATE = "truncate"  # Truncate content to fit
    SLIDING_WINDOW = "sliding_window"  # Use last N events only
    FULL = "full"  # Process full session (may hit token limits)


class LLMConfig:
    """Configuration for LLM agents"""
    def __init__(
        self,
        # Model selection
        analyst_model: str = "claude-3-5-sonnet-20241022",
        critic_model: str = "gpt-4o",
        judge_model: str = "gpt-4o",
        
        # API keys
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        ollama_base_url: str = "http://localhost:11434",
        
        # Custom endpoints
        custom_endpoints: Optional[List[Dict[str, Any]]] = None,
        
        # Fallback configuration
        enable_fallback: bool = False,
        fallback_analyst_model: str = "gpt-4o-mini",
        fallback_critic_model: str = "gpt-4o-mini",
        fallback_judge_model: str = "gpt-4o-mini",
        fallback_retry_after: int = 5,  # Minutes
        
        # Session handling
        session_strategy: SessionHandlingStrategy = SessionHandlingStrategy.TRUNCATE,
        window_size: int = 30,  # Number of events for sliding window
        
        # Model parameters
        temperature: float = 0.7,
        max_tokens_base: int = 4096,
        max_tokens_cap: int = 16000,
        tokens_per_event: int = 100,
        
        # Content truncation limits (for TRUNCATE strategy)
        truncate_content_small: int = 200,  # ≤20 events
        truncate_content_medium: int = 150,  # 21-50 events
        truncate_content_large: int = 100,  # >50 events
        truncate_reasoning_small: int = 300,
        truncate_reasoning_medium: int = 200,
        truncate_reasoning_large: int = 150,
        
        # Custom prompts (optional overrides)
        analyst_prompt_override: Optional[str] = None,
        critic_prompt_override: Optional[str] = None,
        judge_prompt_override: Optional[str] = None
    ):
        # Models
        self.analyst_model = analyst_model
        self.critic_model = critic_model
        self.judge_model = judge_model
        
        # API keys
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        self.google_api_key = google_api_key
        self.ollama_base_url = ollama_base_url
        
        # Custom endpoints
        self.custom_endpoints = custom_endpoints or []
        # Build a mapping of model_id -> endpoint
        self.custom_endpoint_map = {}
        print(f"[DEBUG] Building custom_endpoint_map from {len(self.custom_endpoints)} endpoints")
        for endpoint in self.custom_endpoints:
            print(f"[DEBUG] Endpoint: {endpoint.get('name', 'unnamed')} - {endpoint.get('base_url', 'no-url')}")
            for model in endpoint.get('models', []):
                model_id = model.get('id')
                print(f"[DEBUG]   Adding model: {model_id}")
                self.custom_endpoint_map[model_id] = endpoint
        print(f"[DEBUG] Final custom_endpoint_map has {len(self.custom_endpoint_map)} models: {list(self.custom_endpoint_map.keys())}")
        
        # Fallback configuration
        self.enable_fallback = enable_fallback
        self.fallback_analyst_model = fallback_analyst_model
        self.fallback_critic_model = fallback_critic_model
        self.fallback_judge_model = fallback_judge_model
        self.fallback_retry_after = fallback_retry_after
        
        # Session handling
        self.session_strategy = session_strategy
        self.window_size = window_size
        
        # Model parameters
        self.temperature = temperature
        self.max_tokens_base = max_tokens_base
        self.max_tokens_cap = max_tokens_cap
        self.tokens_per_event = tokens_per_event
        
        # Truncation limits
        self.truncate_content_small = truncate_content_small
        self.truncate_content_medium = truncate_content_medium
        self.truncate_content_large = truncate_content_large
        self.truncate_reasoning_small = truncate_reasoning_small
        self.truncate_reasoning_medium = truncate_reasoning_medium
        self.truncate_reasoning_large = truncate_reasoning_large
        
        # Custom prompts
        self.analyst_prompt_override = analyst_prompt_override
        self.critic_prompt_override = critic_prompt_override
        self.judge_prompt_override = judge_prompt_override
        
    def get_provider(self, model: str) -> ModelProvider:
        """Determine provider from model name"""
        # Check if model is from a custom endpoint
        if model in self.custom_endpoint_map:
            return ModelProvider.OPENAI  # Custom endpoints are OpenAI-compatible
        
        if model.startswith('claude'):
            return ModelProvider.ANTHROPIC
        elif model.startswith('gpt'):
            return ModelProvider.OPENAI
        elif model.startswith('gemini'):
            return ModelProvider.GOOGLE
        else:
            return ModelProvider.OLLAMA
    
    def get_custom_endpoint_config(self, model: str) -> Optional[Dict[str, Any]]:
        """Get custom endpoint configuration for a model"""
        return self.custom_endpoint_map.get(model)
    
    def get_truncation_limits(self, num_events: int) -> tuple[int, int]:
        """
        Get content and reasoning truncation limits based on number of events
        
        Returns: (content_limit, reasoning_limit)
        """
        if self.session_strategy != SessionHandlingStrategy.TRUNCATE:
            # For non-truncate strategies, use small limits (already windowed)
            return self.truncate_content_small, self.truncate_reasoning_small
        
        if num_events <= 20:
            return self.truncate_content_small, self.truncate_reasoning_small
        elif num_events <= 50:
            return self.truncate_content_medium, self.truncate_reasoning_medium
        else:
            return self.truncate_content_large, self.truncate_reasoning_large
    
    def apply_session_strategy(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply session handling strategy to events
        
        Returns: Processed events list
        """
        if self.session_strategy == SessionHandlingStrategy.SLIDING_WINDOW:
            # Use only the last N events
            return events[-self.window_size:] if len(events) > self.window_size else events
        elif self.session_strategy == SessionHandlingStrategy.FULL:
            # Return all events
            return events
        else:  # TRUNCATE
            # Return all events (truncation happens in prompt building)
            return events
    
    def calculate_max_tokens(self, num_events: int, model_id: str) -> int:
        """
        Calculate max_tokens for generation based on event count and model capabilities
        
        Args:
            num_events: Number of events in the session
            model_id: The model identifier to check capabilities
            
        Returns:
            Safe max_tokens value that won't exceed model limits
        """
        # Calculate desired tokens
        desired_tokens = self.max_tokens_base + (num_events * self.tokens_per_event)
        
        # Get model-specific max tokens limit
        model_max = self._get_model_max_tokens(model_id)
        
        # Return minimum of desired, configured cap, and model limit
        return min(desired_tokens, self.max_tokens_cap, model_max)
    
    def _get_model_context_window(self, model_id: str) -> int:
        """Get the total context window (input + output) for a model"""
        model_lower = model_id.lower()
        
        # OpenAI models
        if 'gpt-4o' in model_lower:
            return 128000
        elif 'gpt-4-turbo' in model_lower or 'gpt-4-1106' in model_lower or 'gpt-4-0125' in model_lower:
            return 128000
        elif 'gpt-4-32k' in model_lower:
            return 32768
        elif 'gpt-4' in model_lower:
            return 8192
        elif 'gpt-3.5-turbo-16k' in model_lower:
            return 16384
        elif 'gpt-3.5-turbo' in model_lower:
            return 4096
        
        # Anthropic Claude models
        elif 'claude-3-opus' in model_lower:
            return 200000
        elif 'claude-3-5-sonnet' in model_lower:
            return 200000
        elif 'claude-3-sonnet' in model_lower:
            return 200000
        elif 'claude-3-haiku' in model_lower:
            return 200000
        elif 'claude-2' in model_lower:
            return 100000
        
        # Google Gemini models
        elif 'gemini-1.5-pro' in model_lower:
            return 2000000
        elif 'gemini-1.5-flash' in model_lower:
            return 1000000
        elif 'gemini-pro' in model_lower:
            return 32000
        
        # Default safe limit for unknown models
        else:
            return 8192
    
    def _get_model_max_tokens(self, model_id: str) -> int:
        """Get the maximum output tokens supported by a specific model"""
        model_lower = model_id.lower()
        
        # OpenAI models
        if 'gpt-4o' in model_lower and 'mini' not in model_lower:
            return 16384
        elif 'gpt-4o-mini' in model_lower:
            return 16384
        elif 'gpt-4-turbo' in model_lower or 'gpt-4-1106' in model_lower or 'gpt-4-0125' in model_lower:
            return 4096
        elif 'gpt-4-32k' in model_lower:
            return 4096
        elif 'gpt-4' in model_lower:
            return 8192
        elif 'gpt-3.5-turbo-16k' in model_lower:
            return 4096
        elif 'gpt-3.5-turbo' in model_lower:
            return 4096
        
        # Anthropic Claude models
        elif 'claude-3-opus' in model_lower:
            return 4096
        elif 'claude-3-5-sonnet' in model_lower:
            return 8192
        elif 'claude-3-sonnet' in model_lower:
            return 4096
        elif 'claude-3-haiku' in model_lower:
            return 4096
        elif 'claude-2' in model_lower:
            return 4096
        
        # Google Gemini models
        elif 'gemini-1.5-pro' in model_lower:
            return 8192
        elif 'gemini-1.5-flash' in model_lower:
            return 8192
        elif 'gemini-pro' in model_lower:
            return 2048
        
        # Default safe limit for unknown models
        else:
            return 4096
    
    def _estimate_token_count(self, text: str) -> int:
        """Rough estimate of token count (4 chars ≈ 1 token)"""
        return len(text) // 4


class CognitiveLabel(str, Enum):
    """Cognitive labels based on Information Foraging Theory"""
    FOLLOWING_SCENT = "FollowingScent"
    APPROACHING_SOURCE = "ApproachingSource"
    DIET_ENRICHMENT = "DietEnrichment"
    POOR_SCENT = "PoorScent"
    LEAVING_PATCH = "LeavingPatch"
    FORAGING_SUCCESS = "ForagingSuccess"


class UniversalLLMClient:
    """Universal client for all LLM providers"""
    
    # Class-level tracking for endpoint failures and retry times
    endpoint_failures = {}  # model_id -> last_failure_time
    
    def __init__(self, config: LLMConfig):
        self.config = config
        
    def _should_use_fallback(self, model: str, role: str) -> Optional[str]:
        """
        Check if we should use fallback model due to recent failure
        Returns: fallback_model if should use fallback, None otherwise
        """
        if not self.config.enable_fallback:
            return None
        
        # Check if this is a custom endpoint model
        if model not in self.config.custom_endpoint_map:
            return None
        
        # Check if there's a recent failure
        last_failure = self.endpoint_failures.get(model)
        if last_failure is None:
            return None
        
        # Check if retry period has elapsed
        retry_seconds = self.config.fallback_retry_after * 60
        time_since_failure = time.time() - last_failure
        
        if time_since_failure < retry_seconds:
            # Still in fallback period, return fallback model
            fallback_map = {
                'analyst': self.config.fallback_analyst_model,
                'critic': self.config.fallback_critic_model,
                'judge': self.config.fallback_judge_model,
            }
            return fallback_map.get(role)
        else:
            # Retry period elapsed, clear failure and try custom endpoint again
            del self.endpoint_failures[model]
            return None
    
    def _record_failure(self, model: str):
        """Record a failure for a custom endpoint model"""
        if model in self.config.custom_endpoint_map:
            self.endpoint_failures[model] = time.time()
            print(f"[FALLBACK] Recorded failure for {model}. Will retry after {self.config.fallback_retry_after} minutes.")
        
    async def generate(self, model: str, prompt: str, max_tokens: int = 4096, temperature: Optional[float] = None, role: str = "analyst") -> tuple[str, float]:
        """
        Generate response from any provider with fallback support
        Returns: (response_text, elapsed_time)
        
        Args:
            model: Primary model to use
            prompt: Text prompt
            max_tokens: Maximum tokens
            temperature: Temperature setting
            role: Agent role (for fallback selection)
        """
        # Check if we should use fallback
        fallback_model = self._should_use_fallback(model, role)
        original_model = model
        
        if fallback_model:
            print(f"[FALLBACK] Using fallback model {fallback_model} instead of {model}")
            model = fallback_model
        
        # Debug: Check if model is in custom endpoint map
        if model in self.config.custom_endpoint_map:
            print(f"[DEBUG] Model {model} found in custom_endpoint_map")
        else:
            print(f"[DEBUG] Model {model} NOT in custom_endpoint_map. Available custom models: {list(self.config.custom_endpoint_map.keys())}")
        
        provider = self.config.get_provider(model)
        print(f"[DEBUG] Provider for model {model}: {provider.value}")
        start_time = time.time()
        
        # Use provided temperature or default from config
        temp = temperature if temperature is not None else self.config.temperature
        
        try:
            if provider == ModelProvider.ANTHROPIC:
                response_text = await self._generate_anthropic(model, prompt, max_tokens, temp)
            elif provider == ModelProvider.OPENAI:
                response_text = await self._generate_openai(model, prompt, max_tokens, temp)
            elif provider == ModelProvider.GOOGLE:
                response_text = await self._generate_google(model, prompt, max_tokens, temp)
            elif provider == ModelProvider.OLLAMA:
                response_text = await self._generate_ollama(model, prompt, max_tokens, temp)
            else:
                raise ValueError(f"Unknown provider for model: {model}")
            
            elapsed_time = time.time() - start_time
            return response_text, elapsed_time
            
        except Exception as e:
            # Record failure for custom endpoints to trigger fallback
            self._record_failure(original_model)
            raise Exception(f"Error generating with {provider.value}: {str(e)}")
    
    async def _generate_anthropic(self, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using Anthropic Claude"""
        client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    async def _generate_openai(self, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using OpenAI GPT or custom OpenAI-compatible endpoint"""
        # Check if model is from a custom endpoint
        custom_endpoint = self.config.get_custom_endpoint_config(model)
        
        if custom_endpoint:
            # Use custom endpoint configuration
            # Ensure base_url has /v1 suffix for OpenAI compatibility
            base_url = custom_endpoint['base_url'].rstrip('/')
            if not base_url.endswith('/v1'):
                base_url = f"{base_url}/v1"
            
            print(f"[Custom Endpoint] Using {base_url} for model {model}")
            
            client = openai.OpenAI(
                api_key=custom_endpoint.get('api_key', ''),
                base_url=base_url,
                timeout=60.0  # Set explicit timeout
            )
        else:
            # Use standard OpenAI
            client = openai.OpenAI(api_key=self.config.openai_api_key)
        
        # Wrap synchronous call in thread to avoid blocking
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    async def _generate_google(self, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using Google Gemini"""
        genai.configure(api_key=self.config.google_api_key)
        model_instance = genai.GenerativeModel(model)
        response = model_instance.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
        )
        return response.text
    
    async def _generate_ollama(self, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using local Ollama"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.config.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature
                    }
                }
            )
            response.raise_for_status()
            return response.json()["response"]


LABEL_SCHEMA = """
# Cognitive Label Schema (Information Foraging Theory)

1. **FollowingScent**: User initiates or continues search with a well-formed, targeted query showing clear intent.
   Example: Issuing query "best espresso machine under $500"

2. **ApproachingSource**: User clicks on a result/item based on strong information scent from title/snippet for further investigation.
   Example: Clicking on a promising search result or viewing a recommended movie

3. **DietEnrichment**: User modifies their query to broaden or narrow scope, refining their information need.
   Example: "laptops" → "lightweight laptops for travel"

4. **PoorScent**: User issues new query without clicks, or rates item unexpectedly low, indicating current patch offers no promising scent.
   Example: Query with no clicks on SERP, or giving 1-star to what seemed like relevant content

5. **LeavingPatch**: Session ends after multiple reformulations or attempts without successful interaction.
   Example: User abandons search after several failed query attempts

6. **ForagingSuccess**: User finds what they need (e.g., answer on SERP, accepted solution, satisfactory rating).
   Example: Query with direct answer in featured snippet (no click needed)
"""


class AnalystAgent:
    """Analyst agent for initial cognitive trace analysis"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = UniversalLLMClient(config)
    
    async def analyze(self, session_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze session events and propose cognitive labels
        
        Returns:
            List of decisions, one per event
        """
        # Apply session handling strategy
        processed_events = self.config.apply_session_strategy(session_events)
        
        # Build prompt
        prompt = self._build_prompt(processed_events)
        
        # Calculate max_tokens based on configuration and model capabilities
        max_tokens = self.config.calculate_max_tokens(len(processed_events), self.config.analyst_model)
        
        # Adjust max_tokens based on prompt size to avoid context length errors
        estimated_input_tokens = self.config._estimate_token_count(prompt)
        context_window = self.config._get_model_context_window(self.config.analyst_model)
        available_tokens = context_window - estimated_input_tokens - 100  # 100 token safety buffer
        max_tokens = min(max_tokens, available_tokens)
        
        # Ensure we have at least some tokens for output
        if max_tokens < 500:
            raise Exception(
                f"Session too large ({len(processed_events)} events, ~{estimated_input_tokens} input tokens). "
                f"Please use 'Sliding Window' strategy or reduce window size."
            )
        
        try:
            response_text, elapsed_time = await self.client.generate(
                self.config.analyst_model,
                prompt,
                max_tokens=max_tokens,
                role='analyst'
            )
            
            # Parse response
            decisions = self._parse_response(response_text, processed_events)
            
            return {
                'decisions': decisions,
                'raw_response': response_text,
                'elapsed_time': elapsed_time,
                'events_processed': len(processed_events),
                'events_total': len(session_events)
            }
            
        except Exception as e:
            raise Exception(f"Analyst agent error: {str(e)}")
    
    def _build_prompt(self, session_events: List[Dict[str, Any]]) -> str:
        """Build prompt for analyst agent"""
        
        # Check for custom prompt override
        if self.config.analyst_prompt_override:
            return self.config.analyst_prompt_override
        
        # Get truncation limits from config
        content_limit, _ = self.config.get_truncation_limits(len(session_events))
        
        events_str = ""
        for i, event in enumerate(session_events, 1):
            events_str += f"\nEvent {i}:\n"
            events_str += f"  - ID: {event['event_id']}\n"
            events_str += f"  - Timestamp: {event['timestamp']}\n"
            events_str += f"  - Action: {event['action_type']}\n"
            events_str += f"  - Content: {event['content'][:content_limit]}...\n"
        
        return f"""You are an expert behavioral analyst specializing in Information Foraging Theory. Your task is to analyze user behavior and assign cognitive labels to each event in the session.

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

Provide ONLY the JSON array, no additional text.
"""
    
    def _parse_response(self, response: str, session_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse LLM response into structured decisions"""
        try:
            # Extract JSON from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[start_idx:end_idx]
            decisions = json.loads(json_str)
            
            return decisions
            
        except Exception as e:
            # Fallback: create default decisions
            return [
                {
                    'event_id': event['event_id'],
                    'label': 'FollowingScent',
                    'justification': f'Analysis error: {str(e)}',
                    'confidence': 0.5
                }
                for event in session_events
            ]


class CriticAgent:
    """Critic agent for reviewing analyst's decisions"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = UniversalLLMClient(config)
    
    async def review(
        self,
        session_events: List[Dict[str, Any]],
        analyst_decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Review analyst's decisions and propose alternatives if needed"""
        
        # Apply session handling strategy
        processed_events = self.config.apply_session_strategy(session_events)
        
        # Match decisions to processed events
        if len(processed_events) < len(session_events):
            # Windowed - take last N decisions
            analyst_decisions = analyst_decisions[-len(processed_events):]
        
        prompt = self._build_prompt(processed_events, analyst_decisions)
        
        # Calculate max_tokens based on configuration and model capabilities
        max_tokens = self.config.calculate_max_tokens(len(processed_events), self.config.critic_model)
        
        # Adjust max_tokens based on prompt size to avoid context length errors
        estimated_input_tokens = self.config._estimate_token_count(prompt)
        context_window = self.config._get_model_context_window(self.config.critic_model)
        available_tokens = context_window - estimated_input_tokens - 100
        max_tokens = min(max_tokens, available_tokens)
        
        if max_tokens < 500:
            raise Exception(
                f"Session too large ({len(processed_events)} events, ~{estimated_input_tokens} input tokens). "
                f"Please use 'Sliding Window' strategy or reduce window size."
            )
        
        try:
            response_text, elapsed_time = await self.client.generate(
                self.config.critic_model,
                prompt,
                max_tokens=max_tokens,
                role='critic'
            )
            
            decisions = self._parse_response(response_text, analyst_decisions)
            
            return {
                'decisions': decisions,
                'raw_response': response_text,
                'elapsed_time': elapsed_time
            }
            
        except Exception as e:
            raise Exception(f"Critic agent error: {str(e)}")
    
    def _build_prompt(
        self,
        session_events: List[Dict[str, Any]],
        analyst_decisions: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for critic agent"""
        
        # Check for custom prompt override
        if self.config.critic_prompt_override:
            return self.config.critic_prompt_override
        
        # Get truncation limits from config
        content_limit, reasoning_limit = self.config.get_truncation_limits(len(session_events))
        
        analysis_str = ""
        for i, (event, decision) in enumerate(zip(session_events, analyst_decisions), 1):
            analysis_str += f"\nEvent {i}:\n"
            analysis_str += f"  - Action: {event['action_type']}\n"
            analysis_str += f"  - Content: {event['content'][:content_limit]}...\n"
            analysis_str += f"  - Analyst's Label: {decision['label']}\n"
            analysis_str += f"  - Analyst's Reasoning: {decision['justification'][:reasoning_limit]}...\n"
        
        return f"""You are a critical reviewer specializing in Information Foraging Theory. Your role is to challenge and review the Analyst's cognitive label assignments.

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

Provide ONLY the JSON array, no additional text.
"""
    
    def _parse_response(
        self,
        response: str,
        analyst_decisions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse critic response"""
        try:
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[start_idx:end_idx]
            decisions = json.loads(json_str)
            
            return decisions
            
        except Exception as e:
            # Fallback: agree with analyst
            return [
                {
                    'event_id': d['event_id'],
                    'agreement': 'agree',
                    'label': d['label'],
                    'justification': f'Review error: {str(e)}',
                    'confidence': 0.5
                }
                for d in analyst_decisions
            ]


class JudgeAgent:
    """Judge agent for final decision synthesis"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = UniversalLLMClient(config)
    
    async def decide(
        self,
        session_events: List[Dict[str, Any]],
        analyst_decisions: List[Dict[str, Any]],
        critic_decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Make final decisions synthesizing all perspectives"""
        
        # Apply session handling strategy
        processed_events = self.config.apply_session_strategy(session_events)
        
        # Match decisions to processed events
        if len(processed_events) < len(session_events):
            # Windowed - take last N decisions
            analyst_decisions = analyst_decisions[-len(processed_events):]
            critic_decisions = critic_decisions[-len(processed_events):]
        
        prompt = self._build_prompt(processed_events, analyst_decisions, critic_decisions)
        
        # Calculate max_tokens based on configuration and model capabilities
        max_tokens = self.config.calculate_max_tokens(len(processed_events), self.config.judge_model)
        
        # Adjust max_tokens based on prompt size to avoid context length errors
        estimated_input_tokens = self.config._estimate_token_count(prompt)
        context_window = self.config._get_model_context_window(self.config.judge_model)
        available_tokens = context_window - estimated_input_tokens - 100
        max_tokens = min(max_tokens, available_tokens)
        
        if max_tokens < 500:
            raise Exception(
                f"Session too large ({len(processed_events)} events, ~{estimated_input_tokens} input tokens). "
                f"Please use 'Sliding Window' strategy or reduce window size."
            )
        
        try:
            response_text, elapsed_time = await self.client.generate(
                self.config.judge_model,
                prompt,
                max_tokens=max_tokens,
                role='judge'
            )
            
            decisions = self._parse_response(response_text, fallback_decisions=critic_decisions)
            
            return {
                'decisions': decisions,
                'raw_response': response_text,
                'elapsed_time': elapsed_time
            }
            
        except Exception as e:
            raise Exception(f"Judge agent error: {str(e)}")
    
    def _build_prompt(
        self,
        session_events: List[Dict[str, Any]],
        analyst_decisions: List[Dict[str, Any]],
        critic_decisions: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for judge agent"""
        
        # Check for custom prompt override
        if self.config.judge_prompt_override:
            return self.config.judge_prompt_override
        
        # Get truncation limits from config
        content_limit, reasoning_limit = self.config.get_truncation_limits(len(session_events))
        
        deliberation_str = ""
        for i, (event, analyst, critic) in enumerate(
            zip(session_events, analyst_decisions, critic_decisions), 1
        ):
            deliberation_str += f"\nEvent {i} ({event['event_id']}):\n"
            deliberation_str += f"  - Action: {event['action_type']}\n"
            deliberation_str += f"  - Content: {event['content'][:content_limit]}...\n"
            deliberation_str += f"  - Analyst: {analyst['label']} (confidence: {analyst['confidence']})\n"
            deliberation_str += f"    Reasoning: {analyst['justification'][:reasoning_limit]}...\n"
            deliberation_str += f"  - Critic: {critic['agreement']} - {critic['label']} (confidence: {critic['confidence']})\n"
            deliberation_str += f"    Reasoning: {critic['justification'][:reasoning_limit]}...\n"
        
        return f"""You are the final arbiter in a multi-agent cognitive labeling system. Your role is to synthesize the Analyst's and Critic's perspectives and make the final decision.

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

Provide ONLY the JSON array, no additional text.
"""
    
    def _parse_response(self, response: str, fallback_decisions: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Parse judge response"""
        try:
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[start_idx:end_idx]
            decisions = json.loads(json_str)
            
            return decisions
            
        except Exception as e:
            # If we have fallback decisions (from critic), use them
            if fallback_decisions:
                print(f"[JUDGE] Failed to parse response, using fallback decisions: {str(e)}")
                return [
                    {
                        'event_id': d['event_id'],
                        'final_label': d['label'],
                        'justification': f'Judge parsing failed, using critic decision. Error: {str(e)[:100]}',
                        'confidence': d.get('confidence', 0.5) * 0.8,  # Reduce confidence
                        'flag_for_review': True,
                        'disagreement_score': 0.5
                    }
                    for d in fallback_decisions
                ]
            else:
                raise Exception(f"Failed to parse judge response: {str(e)}")

