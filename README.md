# Inferred Cognitive Traces: Annotation Collection and Tools

<div align="center">

![Cognitive Traces](https://img.shields.io/badge/Cognitive-Traces-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=flat-square)
![Next.js](https://img.shields.io/badge/Next.js-14.0-black?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

**A general and reproducible framework for adding a layer of inferred cognitive traces to existing records of user behavior**

[Quick Start](#quick-start) • [Documentation](#documentation) • [Annotator Tool](#annotator-tool) • [Datasets](#datasets) • [Citation](#citation)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Resource Overview](#resource-overview)
- [Cognitive Annotation Collection](#cognitive-annotation-collection)
- [The Annotator Tool](#the-annotator-tool)
- [Pre-Trained Model](#pre-trained-model)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Cognitive Label Schema](#cognitive-label-schema)
- [Multi-Agent Framework](#multi-agent-framework)
- [API Documentation](#api-documentation)
- [Experimental Validation](#experimental-validation)
- [Contributing](#contributing)
- [License](#license)
- [Citation](#citation)

---

## Overview

This repository contains the complete collection of resources from our work on **inferring cognitive traces from user behavior logs**. Our framework is designed to be:

- **Theory-Grounded**: Based on Information Foraging Theory (IFT) principles
- **Computationally Scalable**: Uses a multi-agent LLM system for large-scale annotation
- **Validated by Experts**: Includes human-in-the-loop verification with high inter-annotator agreement (α=0.78)
- **Reproducible**: All code, data, and models are openly available

### What Are Cognitive Traces?

Cognitive traces are interpretable labels that describe the mental states and strategies underlying observable user actions. While traditional logs tell us *what* users did (e.g., "clicked link 3"), cognitive traces tell us *why* they did it (e.g., "Following strong information scent toward expected answer").

### Why Does This Matter?

Understanding user cognition enables:
- **Better predictions** of user satisfaction and abandonment
- **Improved system design** based on cognitive bottlenecks
- **Richer datasets** for training user-aware AI systems
- **Research insights** into information-seeking behavior

---

## Resource Overview

This repository provides **four main components**:

### 1. Cognitive Annotation Collection

Large-scale annotations for three benchmark datasets:

| Dataset | Domain | Sessions/Users | Total Events | Cognitive Labels |
|---------|--------|----------------|--------------|------------------|
| **AOL-IA** | Web Search | 500K Sessions | ~3.1M Actions | ~3.1M |
| **Stack Overflow** | Technical Q&A | ~2.1M Users | ~16.4M Events | ~16.4M |
| **MovieLens-25M** | Recommendations | 162K Users | ~25M Ratings | ~25M |

**Total: 44.5M+ cognitive labels** spanning multiple information-seeking domains.

### 2. The Annotator Tool

An interactive, web-based application that enables researchers to:
- Upload session-based logs (CSV/JSON)
- Receive AI-assisted cognitive annotations
- Review and correct suggestions with human-in-the-loop workflow
- Export annotated data in analysis-ready formats

### 3. Pre-Trained Model

A lightweight Transformer model (4-layer, 8 attention heads) that provides:
- Fast cognitive label prediction
- 73% F1-score on session abandonment prediction
- 15.5% relative improvement in AUC over behavioral-only baselines

### 4. Source Code & Framework

Complete implementation including:
- Multi-agent annotation pipeline (Analyst, Critic, Judge)
- Backend API (FastAPI + Python)
- Frontend application (Next.js + TypeScript)
- Database schemas and data processing utilities

---

## Cognitive Annotation Collection

### Dataset Statistics

Our initial release provides cognitive annotations demonstrating the flexibility of our framework across different information-seeking domains:

#### AOL-IA (Web Search)
- **500,000 sessions** with ~3.1M user actions
- Includes query sequences, clicks, and archived document content
- High incidence of `PoorScent` and `DietEnrichment` labels
- Typical of open-domain, exploratory search behavior

#### Stack Overflow (Technical Q&A)
- **2.1M users** with ~16.4M events (questions, answers, comments)
- Explicit feedback signals (upvotes, accepted answers)
- Rich context for inferring problem resolution states
- Includes `ApproachingSource` and `ForagingSuccess` patterns

#### MovieLens-25M (Recommender Systems)
- **162K users** with 25M movie ratings and tags
- Cognitive states related to preference formation
- Dominated by `FollowingScent` (e.g., rating multiple films by same director)
- Demonstrates framework applicability beyond search domains

### Data Format

Annotations are provided as **CSV files** with the following schema:

```csv
session_id,event_timestamp,action_type,content_id,cognitive_label,judge_justification
s_001,2006-03-01 12:34:10,QUERY,best_espresso_machine,FollowingScent,"User initiated search with clear, targeted intent"
s_001,2006-03-01 12:34:45,CLICK,doc_4827,ApproachingSource,"Title and snippet provided strong scent for investigation"
s_001,2006-03-01 12:35:20,QUERY,espresso_machine_under_500,DietEnrichment,"Query refinement to narrow scope and add constraint"
```

**Key Fields:**
- `session_id`: Unique identifier for the session or user
- `event_timestamp`: Timestamp of the event
- `action_type`: Type of action (QUERY, CLICK, RATE, etc.)
- `content_id`: Identifier of the query or item
- `cognitive_label`: IFT-based label (see [schema](#cognitive-label-schema))
- `judge_justification`: Natural-language explanation from Judge agent

### Download

Access the complete annotation collection:

```bash
# Clone the repository
git clone https://github.com/searchsim-org/cognitive-traces.git
cd cognitive-traces

# Datasets are in the data/ directory
ls data/
# aol-ia-annotations.csv
# stackoverflow-annotations.csv
# movielens-annotations.csv
```

---

## The Annotator Tool

A key contribution of this work is a **reusable, interactive tool** that transforms our method from a complex pipeline into an accessible annotation platform.

### Features

**Flexible Data Ingestion**
- Upload session logs in CSV or JSON format
- Map your data columns to required fields
- Support for AOL, Stack Overflow, MovieLens, and custom datasets

**AI-Assisted Annotation**
- Automatic cognitive label suggestions with confidence scores
- Multi-agent framework (Analyst → Critic → Judge)
- Transparent reasoning and justifications

**Human-in-the-Loop Workflow**
- Review, accept, or correct AI suggestions
- Dramatically faster than fully manual labeling
- Active learning: system flags uncertain cases for expert review

**Interactive Visualization**
- Session timeline view with event context
- Agent consensus indicators
- Visual label distributions

**Easy Export**
- One-click export in CSV or JSON
- Analysis-ready format with metadata
- Includes agent decisions and justifications

### Web Interface

The Annotator tool provides an intuitive interface with:

1. **Upload Section**: Drag-and-drop file upload with format validation
2. **Session Viewer**: Browse and select sessions from your dataset
3. **Annotation Panel**: View AI-generated labels and agent reasoning
4. **Export Options**: Download annotated data in preferred format

### Usage

See the [Quick Start](#quick-start) section for setup instructions.

---

## Pre-Trained Model

We provide a **lightweight Transformer model** fine-tuned on our annotated datasets for fast cognitive label prediction.

### Model Architecture

- **Base**: 4-layer Transformer encoder with 8 attention heads
- **Input**: 768-dimensional S-BERT embeddings for queries and clicked documents
- **Output**: 6 cognitive labels + confidence scores
- **Parameters**: ~12M trainable parameters

### Performance

Evaluated on **session abandonment prediction** (AOL dataset):

| Metric | Behavioral-Only Baseline | **Cognitive-Enhanced** | Improvement |
|--------|-------------------------|----------------------|-------------|
| Precision | 0.68 | **0.75** | +10.3% |
| Recall | 0.62 | **0.71** | +14.5% |
| F1-Score | 0.65 | **0.73** | +12.3% |
| AUC | 0.71 | **0.82** | +15.5% |

All improvements are statistically significant (p < 0.01).

### Standalone Usage

```python
from cognitive_traces import CognitivePredictor

# Load the pre-trained model
predictor = CognitivePredictor.load('models/cognitive-trace-predictor-v1.0')

# Predict labels for a session
session = {
    'events': [
        {'type': 'QUERY', 'content': 'best espresso machine'},
        {'type': 'CLICK', 'content': 'Product review page content...'},
        {'type': 'QUERY', 'content': 'espresso machine under 500'}
    ]
}

predictions = predictor.predict(session)
# [
#   {'event_id': 0, 'label': 'FollowingScent', 'confidence': 0.89},
#   {'event_id': 1, 'label': 'ApproachingSource', 'confidence': 0.82},
#   {'event_id': 2, 'label': 'DietEnrichment', 'confidence': 0.85}
# ]
```

The model is integrated into the Annotator tool but also available as a standalone component in `models/`.

---

## Quick Start

### Prerequisites

- **Python 3.10+** with Poetry
- **Node.js 18+** with pnpm
- **PostgreSQL** (optional, for persistent storage)
- **Redis** (optional, for batch processing)

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies with Poetry
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your API keys:
# - ANTHROPIC_API_KEY for Claude 3.5 Sonnet (Analyst)
# - OPENAI_API_KEY for GPT-4o (Critic & Judge)

# Run the development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/api/docs
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies with pnpm
pnpm install

# Configure environment
cp .env.local.example .env.local

# Run the development server
pnpm dev

# Application will be available at http://localhost:3000
```

### Docker Setup (Alternative)

```bash
# From project root
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Landing    │  │  Annotator   │  │   Datasets   │     │
│  │     Page     │  │     Tool     │  │   Explorer   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                       Backend (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Multi-Agent Framework                    │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │  │
│  │  │  Analyst   │→ │   Critic   │→ │   Judge    │    │  │
│  │  │  (Claude)  │  │  (GPT-4o)  │  │  (GPT-4o)  │    │  │
│  │  └────────────┘  └────────────┘  └────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Pre-trained │  │   Database   │  │    Celery    │    │
│  │    Model     │  │  (Postgres)  │  │    Queue     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- **FastAPI**: High-performance Python web framework
- **Anthropic Claude 3.5 Sonnet**: Analyst agent (fast, chain-of-thought reasoning)
- **OpenAI GPT-4o**: Critic and Judge agents (nuanced understanding)
- **PostgreSQL**: Persistent storage for sessions and annotations
- **Redis**: Caching and Celery task queue
- **Celery**: Asynchronous batch processing

**Frontend:**
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Radix UI**: Accessible component primitives
- **TanStack Query**: Data fetching and state management
- **Recharts**: Data visualization

---

## Cognitive Label Schema

Our annotation schema is grounded in **Information Foraging Theory (IFT)**, a framework from cognitive science that models human information seeking using analogies from animal foraging behavior.

### The Six Labels

| User Action / Event | IFT Concept | Label | Definition & Example |
|---------------------|-------------|-------|----------------------|
| User issues well-formed query | Following strong scent | **`FollowingScent`** | User initiates/continues search with targeted query. *Ex: "best espresso machine under $500"* |
| User clicks promising result | Approaching information source | **`ApproachingSource`** | Result clicked based on strong scent from snippet/title for further investigation |
| User broadens/narrows query | Enriching information diet | **`DietEnrichment`** | Query modified to broaden or narrow scope, refining information need. *Ex: "laptops" → "lightweight laptops for travel"* |
| User clicks nothing on SERP | Poor scent in current patch | **`PoorScent`** | New query issued without clicks, implying patch offered no promising scent |
| User abandons after many tries | Leaving the patch | **`LeavingPatch`** | Session ends after multiple reformulations without successful interaction |
| User finds answer on SERP | Successful foraging | **`ForagingSuccess`** | Query with no clicks where SERP contains direct answer (e.g., featured snippet) |

### IFT Core Concepts

- **Information Patches**: Result pages, document collections, or item lists
- **Information Scent**: Cues (titles, snippets, genres) that guide users toward valuable items
- **Foraging Strategy**: How users decide to explore, refine, or abandon their search

### Adaptation Across Domains

While designed for search, the schema adapts naturally:

- **Web Search (AOL)**: Direct application of all labels
- **Q&A (Stack Overflow)**: `ApproachingSource` = reading an answer; `ForagingSuccess` = accepting an answer
- **Recommendations (MovieLens)**: `FollowingScent` = rating movies by same actor; `PoorScent` = unexpected low rating

---

## Multi-Agent Framework

Our annotation system uses **three specialized AI agents** that collaborate to produce high-quality, justified labels.

### Agent Roles

#### 1. 🔍 The Analyst (Claude 3.5 Sonnet)

**Purpose**: Initial analysis and label proposal

**Strengths**:
- High-speed reasoning for large-scale annotation
- Excellent at sequential, chain-of-thought tasks
- Processes complete behavioral trace to propose labels

**Output**: For each event, proposes a cognitive label with step-by-step justification

#### 2. 🧐 The Critic (GPT-4o)

**Purpose**: Challenge and review the Analyst's conclusions

**Strengths**:
- Robust general knowledge
- Nuanced understanding of user behavior
- Creative alternative explanation generation

**Output**: Either agrees with Analyst or proposes different label with counter-argument

#### 3. ⚖️ The Judge (GPT-4o)

**Purpose**: Final decision-maker synthesizing all perspectives

**Strengths**:
- Superior ability to weigh conflicting evidence
- Synthesizes complex arguments
- Provides well-reasoned final justification

**Output**: Final cognitive label and comprehensive justification

### Workflow

```
Session Input (queries, clicks, timestamps, content)
           ↓
    ┌─────────────┐
    │   ANALYST   │  Proposes initial labels + justifications
    └─────────────┘
           ↓
    ┌─────────────┐
    │   CRITIC    │  Reviews, challenges, proposes alternatives
    └─────────────┘
           ↓
    ┌─────────────┐
    │    JUDGE    │  Makes final decision + synthesis
    └─────────────┘
           ↓
Annotated Output (labels + multi-agent reasoning chain)
```

### Active Learning

The system automatically **flags the top 1% of cases** where Analyst and Critic have strongest disagreement. These difficult cases are sent to human experts for final ruling, focusing human attention where it's most valuable.

### Prompt Structure

Each agent receives:
1. **Persona**: Role description and expertise domain
2. **Task Instructions**: What to analyze and decide
3. **Schema**: Detailed IFT label definitions with examples
4. **Input Data**: Session events with full context
5. **Output Format**: Structured JSON with label and justification

---

## API Documentation

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoints

#### `POST /annotations/annotate`

Annotate a single session using the multi-agent framework.

**Request Body:**
```json
{
  "session_id": "s_001",
  "events": [
    {
      "event_id": "e1",
      "timestamp": "2006-03-01T12:34:10",
      "action_type": "QUERY",
      "content": "best espresso machine"
    },
    {
      "event_id": "e2",
      "timestamp": "2006-03-01T12:34:45",
      "action_type": "CLICK",
      "content": "Product review page content..."
    }
  ],
  "dataset_type": "custom",
  "use_full_pipeline": true
}
```

**Response:**
```json
{
  "session_id": "s_001",
  "annotated_events": [
    {
      "event_id": "e1",
      "cognitive_label": "FollowingScent",
      "agent_decisions": [
        {
          "agent_name": "analyst",
          "label": "FollowingScent",
          "justification": "User initiated search with clear intent",
          "confidence": 0.89
        }
      ],
      "final_justification": "User demonstrates targeted information seeking",
      "confidence_score": 0.87
    }
  ],
  "processing_time": 2.34,
  "flagged_for_review": false
}
```

#### Other Endpoints

- `POST /annotations/batch-annotate` - Submit batch annotation job
- `POST /annotations/upload` - Upload dataset file (CSV/JSON)
- `GET /sessions` - List annotated sessions with pagination
- `GET /models/info` - Get pre-trained model information
- `POST /models/predict` - Fast prediction using pre-trained model
- `GET /export/csv` | `/export/json` - Export annotations

**Full API documentation** available at `http://localhost:8000/api/docs` when running the backend.

---

## Experimental Validation

### Downstream Task: Session Abandonment Prediction

We evaluated our cognitive traces on **predicting session abandonment** in the AOL dataset—a key indicator of user dissatisfaction.

**Definition**: A session is abandoned if it has 2+ query reformulations and ends with zero clicks, with no activity for 30+ minutes.

### Results

Tested on 96,246 sessions (balanced: 50% abandoned, 50% non-abandoned):

| Model | Precision | Recall | F1-Score | AUC |
|-------|-----------|--------|----------|-----|
| Behavioral-Only Baseline | 0.68 | 0.62 | 0.65 | 0.71 |
| **Cognitive-Enhanced** | **0.75** | **0.71** | **0.73** | **0.82** |
| **Improvement** | **+10.3%** | **+14.5%** | **+12.3%** | **+15.5%** |

*All improvements statistically significant (p < 0.01)*

### Why Cognitive Labels Help

**Behavioral-only models** see raw patterns but miss intent:
- Query → No Click → Query → No Click → End
- Could be exploration or frustration?

**Cognitive-enhanced models** see the user's mental state:
- `FollowingScent` → `PoorScent` → `DietEnrichment` → `PoorScent` → `LeavingPatch`
- **Unambiguous signal** of struggling user → correct abandonment prediction

### Qualitative Insights

Analysis shows cognitive labels are especially valuable for:
- **Ambiguous patterns**: Same actions, different intents
- **Early prediction**: Detecting user frustration before abandonment
- **Explanation**: Understanding *why* predictions are made

---

## Citation

If you use this work in your research, please cite:

```bibtex
@inproceedings{cognitive-traces-2025,
  title={Beyond the Click: A Framework for Inferring Cognitive Traces in Search},
  author={Saber Zerhoudi and Michael Granitzer},
  journal={CoRR},
  year={2025}
}
```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ways to contribute:**
- Report bugs and issues
- Suggest new features or improvements
- Add annotations for new datasets
- Improve the Annotator tool
- Enhance documentation

---

## License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Information Foraging Theory** foundations by Pirolli & Card
- **AOL-IA dataset** by MacAvaney et al.
- **Stack Overflow** data dump from Stack Exchange
- **MovieLens-25M** dataset by Harper & Konstan
- **Anthropic** for Claude 3.5 Sonnet API
- **OpenAI** for GPT-4o API

---

## Contact

For questions, issues, or collaboration inquiries:

- **GitHub Issues**: [Report here](https://github.com/searchsim-org/cognitive-traces/issues)
- **Email**: szerhoudi@acm.org
- **Project Website**: [Coming Soon]

---

<div align="center">

⭐ **Star this repo** if you find it useful!

</div>
