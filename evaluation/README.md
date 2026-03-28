# Experimental Evaluation

This folder contains the code for all experimental validations. The shared model architecture, training, and evaluation scripts are at the root level. Task-specific preprocessing scripts are organized by evaluation type.

## Model Architecture

All experiments use a 4-layer Transformer encoder (768 hidden, 8 heads, CLS pooling) with three model variants:

| Model | Input | Dimensions |
|-------|-------|------------|
| **Behavioral Baseline** | S-BERT (384d) + action-type embedding (32d) | 416d |
| **Cognitive-Enhanced** | + IFT label embedding (32d) | 448d |
| **Shuffled Control** | Same as cognitive, labels randomly permuted per session | 448d |

S-BERT model: `all-MiniLM-L6-v2`. Action-type and IFT label embeddings are learned.

## Evaluation Types

### `cross_dataset/` — Cross-Dataset Evaluation (Paper Section 4)

The main evaluation: 4 prediction tasks applied to all 3 datasets (12 experiments total), with shuffled-label control.

**Tasks:**
| Task | Script | Description |
|------|--------|-------------|
| Session Continuation | `data_preprocessing_session_continuation.py` | Predict whether session continues after event t |
| Positive Outcome | `data_preprocessing_positive_outcome.py` | Predict whether next interaction is positive |
| Exploration vs. Exploitation | `data_preprocessing_explore_exploit.py` | Predict whether next action explores or exploits |
| Early Success | `data_preprocessing_session_success_early.py` | From first 3 events, predict full-session success |

**Datasets:** AOL (22,039 sessions), Stack Overflow (18,629), MovieLens (10,274)

**Key finding:** Cognitive labels help most where behavioral signals are weakest. MovieLens shows avg +7.7% F1 over baseline; AOL and SO show minimal improvement because their action types are already informative.

### `session_outcome/` — Session Outcome Prediction

Predicts whether a search session ends in success or failure using the first 50% of session events. Originally evaluated on AOL data only.

### `struggle_recovery/` — Struggle Recovery Prediction

For sessions starting in a struggle state, predicts whether the user recovers to success using the first 40% of events. Originally evaluated on AOL data only.

## Directory Structure

```
evaluation/
├── README.md
├── requirements.txt
├── model.py                 # Transformer model (3 variants)
├── dataset.py               # Dataset loader with pre-computed S-BERT embeddings
├── train.py                 # Training (behavioral + cognitive + shuffled)
├── evaluate.py              # 3-way evaluation with comparison metrics
│
├── cross_dataset/           # 4 tasks × 3 datasets (paper Section 4)
│   ├── data_preprocessing_session_continuation.py
│   ├── data_preprocessing_positive_outcome.py
│   ├── data_preprocessing_explore_exploit.py
│   └── data_preprocessing_session_success_early.py
│
├── session_outcome/         # Session outcome prediction
│   ├── data_preprocessing_session_outcome.py
│   └── results/model_comparison.json
│
└── struggle_recovery/       # Struggle recovery prediction
    ├── data_preprocessing_struggle_recovery.py
    └── results/model_comparison.json
```

## Reproducing Results

### Prerequisites

```bash
pip install -r requirements.txt
```

Datasets are available on HuggingFace:

```python
from datasets import load_dataset
aol = load_dataset("searchsim/cognitive-traces-aol")
so  = load_dataset("searchsim/cognitive-traces-stackoverflow")
ml  = load_dataset("searchsim/cognitive-traces-movielens")
```

### Run a Single Experiment

```bash
# Example: Session Continuation on MovieLens

# 1. Export dataset to CSV
python -c "
from datasets import load_dataset
ds = load_dataset('searchsim/cognitive-traces-movielens')
ds['train'].to_pandas().to_csv('movielens_traces.csv', index=False)
"

# 2. Preprocess
python cross_dataset/data_preprocessing_session_continuation.py \
    movielens_traces.csv --output-dir data/session_continuation_ml --seed 42

# 3. Train all 3 model variants
python train.py --data-dir data/session_continuation_ml \
    --output-dir checkpoints/session_continuation_ml \
    --model-type all --num-epochs 20 --batch-size 64 \
    --learning-rate 5e-5 --patience 7

# 4. Evaluate with 3-way comparison
python evaluate.py \
    --checkpoint checkpoints/session_continuation_ml/cognitive_enhanced_best.pt \
    --model-type cognitive \
    --data-dir data/session_continuation_ml \
    --output-dir results/session_continuation_ml \
    --compare checkpoints/session_continuation_ml/behavioral_baseline_best.pt \
    --shuffled-checkpoint checkpoints/session_continuation_ml/shuffled_label_best.pt
```

### Training Configuration

| Parameter | Value |
|-----------|-------|
| Optimizer | Adam |
| Learning rate | 5e-5 |
| Batch size | 64 |
| Max epochs | 20 |
| Early stopping | Patience 7 (validation F1) |
| Loss | Binary cross-entropy, class-balanced (majority downsampling) |
| Splits | 80/10/10 user-based |
| Seed | 42 |
| Hardware | Single NVIDIA A100 GPU |
