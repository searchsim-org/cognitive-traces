"""
LLM Agent implementations for cognitive trace annotation
"""

import anthropic
import openai
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import time
import httpx
import google.generativeai as genai


class ModelProvider(str, Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    OLLAMA = "ollama"


class LLMConfig:
    """Configuration for LLM agents"""
    def __init__(
        self,
        analyst_model: str = "claude-3-5-sonnet-20241022",
        critic_model: str = "gpt-4o",
        judge_model: str = "gpt-4o",
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        ollama_base_url: str = "http://localhost:11434"
    ):
        self.analyst_model = analyst_model
        self.critic_model = critic_model
        self.judge_model = judge_model
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        self.google_api_key = google_api_key
        self.ollama_base_url = ollama_base_url
        
    def get_provider(self, model: str) -> ModelProvider:
        """Determine provider from model name"""
        if model.startswith('claude'):
            return ModelProvider.ANTHROPIC
        elif model.startswith('gpt'):
            return ModelProvider.OPENAI
        elif model.startswith('gemini'):
            return ModelProvider.GOOGLE
        else:
            return ModelProvider.OLLAMA


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
    
    def __init__(self, config: LLMConfig):
        self.config = config
        
    async def generate(self, model: str, prompt: str, max_tokens: int = 4096) -> tuple[str, float]:
        """
        Generate response from any provider
        Returns: (response_text, elapsed_time)
        """
        provider = self.config.get_provider(model)
        start_time = time.time()
        
        try:
            if provider == ModelProvider.ANTHROPIC:
                response_text = await self._generate_anthropic(model, prompt, max_tokens)
            elif provider == ModelProvider.OPENAI:
                response_text = await self._generate_openai(model, prompt, max_tokens)
            elif provider == ModelProvider.GOOGLE:
                response_text = await self._generate_google(model, prompt, max_tokens)
            elif provider == ModelProvider.OLLAMA:
                response_text = await self._generate_ollama(model, prompt, max_tokens)
            else:
                raise ValueError(f"Unknown provider for model: {model}")
            
            elapsed_time = time.time() - start_time
            return response_text, elapsed_time
            
        except Exception as e:
            raise Exception(f"Error generating with {provider.value}: {str(e)}")
    
    async def _generate_anthropic(self, model: str, prompt: str, max_tokens: int) -> str:
        """Generate using Anthropic Claude"""
        client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    async def _generate_openai(self, model: str, prompt: str, max_tokens: int) -> str:
        """Generate using OpenAI GPT"""
        client = openai.OpenAI(api_key=self.config.openai_api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    async def _generate_google(self, model: str, prompt: str, max_tokens: int) -> str:
        """Generate using Google Gemini"""
        genai.configure(api_key=self.config.google_api_key)
        model_instance = genai.GenerativeModel(model)
        response = model_instance.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7
            )
        )
        return response.text
    
    async def _generate_ollama(self, model: str, prompt: str, max_tokens: int) -> str:
        """Generate using local Ollama"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.config.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens
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
        prompt = self._build_prompt(session_events)
        
        try:
            response_text, elapsed_time = await self.client.generate(
                self.config.analyst_model,
                prompt,
                max_tokens=4096
            )
            
            # Parse response
            decisions = self._parse_response(response_text, session_events)
            
            return {
                'decisions': decisions,
                'raw_response': response_text,
                'elapsed_time': elapsed_time
            }
            
        except Exception as e:
            raise Exception(f"Analyst agent error: {str(e)}")
    
    def _build_prompt(self, session_events: List[Dict[str, Any]]) -> str:
        """Build prompt for analyst agent"""
        
        events_str = ""
        for i, event in enumerate(session_events, 1):
            events_str += f"\nEvent {i}:\n"
            events_str += f"  - ID: {event['event_id']}\n"
            events_str += f"  - Timestamp: {event['timestamp']}\n"
            events_str += f"  - Action: {event['action_type']}\n"
            events_str += f"  - Content: {event['content'][:200]}...\n"
        
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
        
        prompt = self._build_prompt(session_events, analyst_decisions)
        
        try:
            response_text, elapsed_time = await self.client.generate(
                self.config.critic_model,
                prompt,
                max_tokens=4096
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
        
        analysis_str = ""
        for i, (event, decision) in enumerate(zip(session_events, analyst_decisions), 1):
            analysis_str += f"\nEvent {i}:\n"
            analysis_str += f"  - Action: {event['action_type']}\n"
            analysis_str += f"  - Content: {event['content'][:200]}...\n"
            analysis_str += f"  - Analyst's Label: {decision['label']}\n"
            analysis_str += f"  - Analyst's Reasoning: {decision['justification']}\n"
        
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
        
        prompt = self._build_prompt(session_events, analyst_decisions, critic_decisions)
        
        try:
            response_text, elapsed_time = await self.client.generate(
                self.config.judge_model,
                prompt,
                max_tokens=4096
            )
            
            decisions = self._parse_response(response_text)
            
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
        
        deliberation_str = ""
        for i, (event, analyst, critic) in enumerate(
            zip(session_events, analyst_decisions, critic_decisions), 1
        ):
            deliberation_str += f"\nEvent {i} ({event['event_id']}):\n"
            deliberation_str += f"  - Action: {event['action_type']}\n"
            deliberation_str += f"  - Content: {event['content'][:150]}...\n"
            deliberation_str += f"  - Analyst: {analyst['label']} (confidence: {analyst['confidence']})\n"
            deliberation_str += f"    Reasoning: {analyst['justification'][:200]}...\n"
            deliberation_str += f"  - Critic: {critic['agreement']} - {critic['label']} (confidence: {critic['confidence']})\n"
            deliberation_str += f"    Reasoning: {critic['justification'][:200]}...\n"
        
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
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
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
            raise Exception(f"Failed to parse judge response: {str(e)}")

