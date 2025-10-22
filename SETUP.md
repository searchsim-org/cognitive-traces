# Quick Setup Guide

This guide will help you get the Cognitive Traces project up and running on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Download Node.js](https://nodejs.org/)
- **pnpm**: Install with `npm install -g pnpm`
- **Poetry**: Install with `curl -sSL https://install.python-poetry.org | python3 -`
- **PostgreSQL** (optional): [Download PostgreSQL](https://www.postgresql.org/download/)
- **Redis** (optional): [Download Redis](https://redis.io/download)

## Option 1: Local Development Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/searchsim-org/cognitive-traces.git
cd cognitive-traces
```

### Step 2: Set Up Backend

```bash
# Navigate to backend directory
cd backend

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys:
# - ANTHROPIC_API_KEY=your_anthropic_key
# - OPENAI_API_KEY=your_openai_key

# (Optional) Initialize database
# If using PostgreSQL, create the database first:
# createdb cognitive_traces
poetry run alembic upgrade head

# Start the backend server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/api/docs`

### Step 3: Set Up Frontend

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
pnpm install

# Copy environment file
cp .env.local.example .env.local

# Start the development server
pnpm dev
```

The frontend will be available at `http://localhost:3000`

### Step 4: Verify Setup

1. Open `http://localhost:3000` in your browser
2. You should see the Cognitive Traces landing page
3. Navigate to the Annotator tool
4. Try uploading a sample CSV file

## Option 2: Docker Setup

The easiest way to get started is using Docker Compose:

### Step 1: Prerequisites

- Install [Docker](https://docs.docker.com/get-docker/)
- Install [Docker Compose](https://docs.docker.com/compose/install/)

### Step 2: Configure Environment

```bash
# Clone the repository
git clone https://github.com/searchsim-org/cognitive-traces.git
cd cognitive-traces

# Set up backend environment
cd backend
cp .env.example .env
# Edit .env and add your API keys

cd ..
```

### Step 3: Start All Services

```bash
# From project root
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Step 4: Run Migrations

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head
```

## Getting API Keys

### Anthropic Claude API

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy and add to `.env` as `ANTHROPIC_API_KEY`

### OpenAI API

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy and add to `.env` as `OPENAI_API_KEY`

## Verify Installation

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# Expected response: {"status":"healthy"}
```

### Test Frontend

1. Open browser to `http://localhost:3000`
2. Should see the landing page
3. Click "Try Annotator Tool"
4. Should navigate to `/annotator`

### Test API

```bash
# Get model info
curl http://localhost:8000/api/v1/models/info

# Should return model information JSON
```

## Running Tests

### Backend Tests

```bash
cd backend
poetry run pytest
poetry run pytest --cov=app tests/
```

### Frontend Tests

```bash
cd frontend
pnpm test
pnpm type-check
pnpm lint
```

## Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError`
```bash
# Solution: Reinstall dependencies
poetry install --no-cache
```

**Issue**: Database connection error
```bash
# Solution: Check PostgreSQL is running
# For Docker: docker-compose ps
# For local: pg_isready
```

**Issue**: API key errors
```bash
# Solution: Verify .env file has correct keys
cat backend/.env | grep API_KEY
```

### Frontend Issues

**Issue**: `Cannot find module` errors
```bash
# Solution: Clear cache and reinstall
rm -rf node_modules .next
pnpm install
```

**Issue**: API connection refused
```bash
# Solution: Verify backend is running
curl http://localhost:8000/health
```

**Issue**: Port already in use
```bash
# Solution: Change port or kill process
# Change port: pnpm dev -- -p 3001
# Kill process: lsof -ti:3000 | xargs kill
```

## Next Steps

Once setup is complete:

1. **Read the documentation**: Check out the main [README.md](README.md)
2. **Try the annotator**: Upload a sample dataset and test annotations
3. **Explore the API**: Visit `http://localhost:8000/api/docs`
4. **Review examples**: Check the `examples/` directory (coming soon)
5. **Join the community**: Contribute or ask questions on GitHub

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Search [existing issues](https://github.com/searchsim-org/cognitive-traces/issues)
3. Open a [new issue](https://github.com/searchsim-org/cognitive-traces/issues/new)



