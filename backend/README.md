# Cognitive Traces Backend

FastAPI backend for the Cognitive Traces annotation framework.

## Setup

1. Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the development server:
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Architecture

- **FastAPI**: Modern, fast web framework
- **Anthropic Claude 3.5 Sonnet**: Analyst agent
- **OpenAI GPT-4o**: Critic and Judge agents
- **PostgreSQL**: Persistent storage
- **Redis**: Caching and task queue
- **Celery**: Asynchronous batch processing

