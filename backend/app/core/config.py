"""
Application configuration and settings
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Cognitive Traces API"
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins"
    )
    
    # AI Models
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key for Claude")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key for GPT-4o")
    
    # Analyst Model (Claude 3.5 Sonnet)
    ANALYST_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Critic and Judge Model (GPT-4o)
    CRITIC_MODEL: str = "gpt-4o"
    JUDGE_MODEL: str = "gpt-4o"
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/cognitive_traces",
        description="PostgreSQL database URL"
    )
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", description="Celery result backend")
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "uploads"
    
    # Annotation Settings
    BATCH_SIZE: int = 50
    ACTIVE_LEARNING_THRESHOLD: float = 0.01  # Top 1% disagreement cases
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

