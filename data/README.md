# Datasets

This directory contains **small excerpts** from the full cognitive trace datasets, useful for testing the annotation pipeline and understanding the expected input/output format.

## Full Datasets on HuggingFace

The complete annotated datasets (532,673 events across 50,942 sessions) are hosted on HuggingFace:

| Dataset | Sessions | Events | HuggingFace |
|---------|----------|--------|-------------|
| **AOL Search Sessions** | 22,039 | 245,786 | [searchsim/cognitive-traces-aol](https://huggingface.co/datasets/searchsim/cognitive-traces-aol) |
| **Stack Overflow Q&A** | 18,629 | 175,326 | [searchsim/cognitive-traces-stackoverflow](https://huggingface.co/datasets/searchsim/cognitive-traces-stackoverflow) |
| **MovieLens Ratings** | 10,274 | 111,561 | [searchsim/cognitive-traces-movielens](https://huggingface.co/datasets/searchsim/cognitive-traces-movielens) |

### Quick Start

```python
from datasets import load_dataset

# Load any dataset
aol = load_dataset("searchsim/cognitive-traces-aol")
stackoverflow = load_dataset("searchsim/cognitive-traces-stackoverflow")
movielens = load_dataset("searchsim/cognitive-traces-movielens")

# Access the data
df = aol["train"].to_pandas()
```

## Local Excerpts (50 sessions each)

- `aol_annotated.csv` — 540 events from 50 AOL search sessions
- `stackoverflow_annotated.csv` — 428 events from 50 Stack Overflow sessions
- `movielens_annotated.csv` — 447 events from 50 MovieLens sessions

These excerpts are sampled directly from the HuggingFace datasets and share the same schema.

## Column Schema

| Column | Description |
|--------|-------------|
| `session_id` | Unique session identifier |
| `event_id` | Unique event identifier |
| `event_timestamp` | When the event occurred |
| `action_type` | Type of action (QUERY, CLICK, RATE, POST_QUESTION, etc.) |
| `content` | Event content (query text, URL, movie rating, etc.) |
| `cognitive_label` | Final IFT cognitive state label |
| `analyst_label` | Label from the Analyst agent |
| `analyst_justification` | Analyst reasoning |
| `critic_label` | Label from the Critic agent |
| `critic_agreement` | Whether Critic agreed with Analyst |
| `critic_justification` | Critic reasoning |
| `judge_justification` | Judge's final reasoning |
| `confidence_score` | Model confidence (0–1) |
| `disagreement_score` | Inter-agent disagreement measure |
| `flagged_for_review` | Whether human review is recommended |
| `pipeline_mode` | Annotation pipeline mode used |
