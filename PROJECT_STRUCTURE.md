# Project Structure

This document provides an overview of the Cognitive Traces project organization.

```
cognitive-traces/
│
├── backend/                    # Python FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI application entry point
│   │   │
│   │   ├── api/               # API routes
│   │   │   ├── __init__.py
│   │   │   └── endpoints/
│   │   │       ├── annotations.py    # Annotation endpoints
│   │   │       ├── sessions.py       # Session management
│   │   │       ├── models.py         # Model endpoints
│   │   │       └── export.py         # Data export
│   │   │
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py     # Settings and environment variables
│   │   │   └── security.py   # Authentication (future)
│   │   │
│   │   ├── schemas/           # Pydantic models
│   │   │   ├── annotation.py  # Annotation request/response models
│   │   │   ├── session.py     # Session models
│   │   │   └── model.py       # ML model schemas
│   │   │
│   │   ├── services/          # Business logic
│   │   │   ├── annotation_service.py  # Multi-agent annotation
│   │   │   ├── model_service.py       # Pre-trained model inference
│   │   │   └── export_service.py      # Data export logic
│   │   │
│   │   ├── agents/            # Multi-agent framework
│   │   │   ├── analyst.py     # Claude 3.5 Sonnet analyst
│   │   │   ├── critic.py      # GPT-4o critic
│   │   │   └── judge.py       # GPT-4o judge
│   │   │
│   │   ├── models/            # Database models (SQLAlchemy)
│   │   │   ├── session.py
│   │   │   ├── annotation.py
│   │   │   └── user.py
│   │   │
│   │   └── utils/             # Utility functions
│   │       ├── data_processing.py
│   │       └── validation.py
│   │
│   ├── tests/                 # Backend tests
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_agents/
│   │
│   ├── alembic/               # Database migrations
│   │   └── versions/
│   │
│   ├── pyproject.toml         # Poetry dependencies
│   ├── .env.example           # Environment template
│   ├── Dockerfile             # Backend Docker config
│   └── README.md              # Backend documentation
│
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/               # Next.js 14 App Router
│   │   │   ├── layout.tsx     # Root layout
│   │   │   ├── page.tsx       # Landing page
│   │   │   ├── globals.css    # Global styles
│   │   │   │
│   │   │   ├── annotator/     # Annotator tool
│   │   │   │   └── page.tsx
│   │   │   │
│   │   │   └── datasets/      # Dataset explorer
│   │   │       └── page.tsx
│   │   │
│   │   ├── components/        # React components
│   │   │   ├── Providers.tsx  # Context providers
│   │   │   │
│   │   │   ├── layout/        # Layout components
│   │   │   │   ├── Navigation.tsx
│   │   │   │   └── Footer.tsx
│   │   │   │
│   │   │   ├── home/          # Landing page components
│   │   │   │   ├── Hero.tsx
│   │   │   │   ├── Features.tsx
│   │   │   │   ├── Statistics.tsx
│   │   │   │   └── GetStarted.tsx
│   │   │   │
│   │   │   ├── annotator/     # Annotator components
│   │   │   │   ├── UploadSection.tsx
│   │   │   │   ├── SessionViewer.tsx
│   │   │   │   ├── AnnotationPanel.tsx
│   │   │   │   └── ExportSection.tsx
│   │   │   │
│   │   │   └── datasets/      # Dataset components
│   │   │       └── DatasetCard.tsx
│   │   │
│   │   ├── lib/               # Utility libraries
│   │   │   ├── api.ts         # API client
│   │   │   └── utils.ts       # Helper functions
│   │   │
│   │   └── types/             # TypeScript types
│   │       ├── annotation.ts
│   │       └── session.ts
│   │
│   ├── public/                # Static assets
│   │   ├── images/
│   │   └── icons/
│   │
│   ├── package.json           # NPM dependencies
│   ├── tsconfig.json          # TypeScript config
│   ├── tailwind.config.ts     # Tailwind CSS config
│   ├── next.config.js         # Next.js config
│   ├── .env.local.example     # Environment template
│   ├── Dockerfile             # Frontend Docker config
│   └── README.md              # Frontend documentation
│
├── data/                       # Annotated datasets (not in repo)
│   ├── aol-ia-annotations.csv
│   ├── stackoverflow-annotations.csv
│   └── movielens-annotations.csv
│
├── models/                     # Pre-trained models (not in repo)
│   └── cognitive-trace-predictor-v1.0/
│       ├── config.json
│       ├── pytorch_model.bin
│       └── tokenizer/
│
├── docs/                       # Additional documentation
│   ├── api-reference.md
│   ├── dataset-format.md
│   └── multi-agent-framework.md
│
├── examples/                   # Usage examples
│   ├── python/
│   │   ├── annotate_session.py
│   │   └── batch_processing.py
│   └── notebooks/
│       └── getting_started.ipynb
│
├── scripts/                    # Utility scripts
│   ├── download_datasets.sh
│   ├── setup_dev.sh
│   └── run_tests.sh
│
├── .github/                    # GitHub configuration
│   ├── workflows/              # CI/CD workflows
│   │   ├── backend-tests.yml
│   │   ├── frontend-tests.yml
│   │   └── deploy.yml
│   └── ISSUE_TEMPLATE/
│
├── README.md                   # Main project README
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT License
├── SETUP.md                    # Quick setup guide
├── PROJECT_STRUCTURE.md        # This file
├── .gitignore                  # Git ignore rules
└── docker-compose.yml          # Docker Compose configuration
```

## Key Directories

### Backend (`/backend`)

**Purpose**: FastAPI-based REST API for cognitive annotation

**Key Files**:
- `app/main.py`: Application entry point with route registration
- `app/api/endpoints/`: REST API endpoints organized by resource
- `app/services/`: Business logic and multi-agent framework
- `app/schemas/`: Pydantic models for request/response validation
- `pyproject.toml`: Poetry dependency management

### Frontend (`/frontend`)

**Purpose**: Next.js web application for interactive annotation

**Key Files**:
- `src/app/page.tsx`: Landing page
- `src/app/annotator/page.tsx`: Main annotator interface
- `src/components/`: Reusable React components
- `package.json`: NPM dependencies managed by pnpm

### Data (`/data`)

**Purpose**: Storage for annotated datasets

**Note**: Large datasets are not stored in the repository. Download from releases or generate using the framework.

### Models (`/models`)

**Purpose**: Pre-trained cognitive label prediction models

**Note**: Model files are too large for the repository. Download from releases or train your own.

## Data Flow

```
User Input (CSV/JSON)
        ↓
Frontend Upload Component
        ↓
Backend API (/annotations/upload)
        ↓
Data Processing & Validation
        ↓
Multi-Agent Framework
  ├─ Analyst (Claude 3.5 Sonnet)
  ├─ Critic (GPT-4o)
  └─ Judge (GPT-4o)
        ↓
Database Storage (PostgreSQL)
        ↓
Frontend Display & Review
        ↓
Export (CSV/JSON)
```

## Component Relationships

### Backend Services

- **AnnotationService**: Orchestrates multi-agent annotation
  - Uses: Analyst, Critic, Judge agents
  - Stores: Session and Annotation models
  - Validates: Using Pydantic schemas

- **ModelService**: Handles pre-trained model inference
  - Loads: PyTorch models from `/models`
  - Provides: Fast predictions as alternative to agents

- **ExportService**: Generates downloadable datasets
  - Formats: CSV, JSON
  - Includes: Full annotation metadata

### Frontend Components

- **AnnotatorPage**: Main orchestrator
  - Contains: UploadSection, SessionViewer, AnnotationPanel
  - Manages: Session state and selection

- **SessionViewer**: Display session list
  - Fetches: Session data from API
  - Emits: Session selection events

- **AnnotationPanel**: Show agent decisions
  - Displays: Analyst, Critic, Judge outputs
  - Allows: Human review and correction

## Dependencies

### Backend Dependencies

**Core**:
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `sqlalchemy`: ORM
- `alembic`: Database migrations

**AI/ML**:
- `anthropic`: Claude API client
- `openai`: GPT API client
- `sentence-transformers`: Text embeddings
- `torch`: PyTorch for models

**Infrastructure**:
- `celery`: Task queue
- `redis`: Caching and queue backend
- `psycopg2-binary`: PostgreSQL driver

### Frontend Dependencies

**Core**:
- `next`: React framework
- `react`: UI library
- `typescript`: Type safety

**UI**:
- `tailwindcss`: Styling
- `@radix-ui/*`: Accessible components
- `lucide-react`: Icons
- `framer-motion`: Animations

**Data**:
- `@tanstack/react-query`: Data fetching
- `axios`: HTTP client
- `zustand`: State management

## Development Workflow

1. **Backend Development**: Edit files in `/backend/app/`
2. **Frontend Development**: Edit files in `/frontend/src/`
3. **API Changes**: Update schemas in `/backend/app/schemas/`
4. **Database Changes**: Create migration in `/backend/alembic/versions/`
5. **UI Changes**: Modify components in `/frontend/src/components/`

## Testing Structure

```
backend/tests/
├── test_api/          # API endpoint tests
├── test_services/     # Service layer tests
├── test_agents/       # Multi-agent framework tests
└── conftest.py        # Pytest configuration

frontend/src/
└── components/
    └── __tests__/     # Component tests
```

## Documentation Structure

- **README.md**: Overview and quick start
- **SETUP.md**: Detailed setup instructions
- **CONTRIBUTING.md**: Contribution guidelines
- **PROJECT_STRUCTURE.md**: This file
- **docs/**: Detailed technical documentation

## Security Considerations

- API keys stored in `.env` files (not committed)
- Database credentials in environment variables
- CORS properly configured in backend
- Input validation using Pydantic schemas

## Docker Configuration

- **docker-compose.yml**: Multi-service orchestration
- **backend/Dockerfile**: Python API container
- **frontend/Dockerfile**: Next.js container
- Includes: PostgreSQL, Redis services

---

For more information, see the main [README.md](README.md) or [CONTRIBUTING.md](CONTRIBUTING.md).

