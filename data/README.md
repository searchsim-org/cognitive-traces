# Datasets

This directory contains **example datasets** that demonstrate the input format and output structure of the Cognitive Traces Annotator.

<div align="center" style="margin: 0px 0 30px; padding: 0px 10px 10px; color: #856404; background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: .25rem;">

### 🚧 Important Notice 🚧

These datasets are **excerpts** from the full-sized datasets used in our research. They are provided here for: (1) testing the annotation pipeline, (2) understanding the expected input/output format, and (3) quick experimentation and validation

</div>

## Full Dataset Access

The **complete datasets** with all cognitive trace annotations are being made available on Zenodo.

**Stack Overflow Dataset**: [https://doi.org/10.5281/zenodo.17523285](https://doi.org/10.5281/zenodo.17523285) 

**AOL & MovieLens Datasets**: *Coming soon*

## Available Datasets

### AOL Search Sessions (1,000 sessions)
- **Input**: `aol_1k_input.csv` - Raw search session data
- **Output**: `aol_1k_annotated.csv` - Cognitive traces with multi-agent annotations

### MovieLens User Interactions
- **Input**: `movielens_input.csv` - User-movie interaction data
- **Output**: `movielens_annotated.csv` - Cognitive traces with multi-agent annotations

### StackOverflow User Interactions
- **Input**: `stackoverflow_input.csv` - Technical Q&A interaction data
- **Output**: `stackoverflow_annotated.csv` - Cognitive traces with multi-agent annotations


## Format Details

### Input Format
CSV files with columns:
- `session_id`: Unique identifier for each session
- `event_id`: Unique identifier for each event
- `timestamp`: When the event occurred
- `action_type`: Type of action (QUERY, CLICK, SERP_VIEW, etc.)
- `content`: Event content (query text, URL, etc.)

### Output Format (Annotated)
CSV files with additional columns:
- `cognitive_label`: Final cognitive state label
- `analyst_label`, `critic_label`: Multi-agent labels
- `analyst_justification`, `critic_justification`, `judge_justification`: Reasoning
- `confidence_score`: Model confidence (0-1)
- `disagreement_score`: Agent disagreement measure
- `flagged_for_review`: Whether human review is recommended
- `user_override`: Whether a human annotator modified the label



