# Session Abandonment Prediction Models

This directory contains the implementation of session abandonment prediction models as described in the paper.

## Overview

We train and evaluate two models for predicting session abandonment:

1. **Behavioral-Only Baseline**: Uses S-BERT embeddings of queries and clicked documents
2. **Cognitive-Enhanced Model**: Augments behavioral signals with cognitive trace labels

Both models use the same core architecture:
- 4-layer Transformer encoder with 8 attention heads
- [CLS] token for sequence representation
- Binary classification via sigmoid activation

## Setup

### Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Or if you're using the project's Poetry environment:

```bash
cd ..
poetry install
```

### Data Preparation

First, preprocess your annotated AOL data:

```bash
python data_preprocessing.py /path/to/annotated_aol.csv \
  --output-dir data/processed \
  --seed 42
```

This script will:
- Identify abandoned sessions (2+ queries, ends with zero clicks, 30+ min inactivity)
- Create a balanced dataset (50% abandoned, 50% non-abandoned)
- Split into train/val/test (80%/10%/10%) with no user overlap

**Expected Output:**
```
data/processed/
├── train.csv              # Training set
├── val.csv                # Validation set
├── test.csv               # Test set
├── session_labels.json    # Session-level labels (0 or 1)
├── metadata.json          # Dataset statistics
└── embedding_cache/       # Cached S-BERT embeddings (created during training)
```

## Training

### Train Both Models

```bash
python train.py \
  --data-dir data/processed \
  --output-dir checkpoints \
  --model-type both \
  --num-epochs 20 \
  --batch-size 32 \
  --learning-rate 1e-4 \
  --patience 5
```

### Train Individual Models

**Behavioral-Only Baseline:**
```bash
python train.py \
  --data-dir data/processed \
  --model-type behavioral \
  --num-epochs 20
```

**Cognitive-Enhanced:**
```bash
python train.py \
  --data-dir data/processed \
  --model-type cognitive \
  --num-epochs 20
```

### Training Arguments

- `--data-dir`: Directory with preprocessed data (required)
- `--output-dir`: Directory to save checkpoints (default: `checkpoints`)
- `--model-type`: Which model(s) to train: `behavioral`, `cognitive`, or `both` (default: `both`)
- `--num-epochs`: Number of training epochs (default: 20)
- `--batch-size`: Batch size (default: 32)
- `--learning-rate`: Learning rate for Adam optimizer (default: 1e-4)
- `--patience`: Early stopping patience in epochs (default: 5)
- `--device`: Device to use: `cpu` or `cuda` (auto-detect if not specified)

### Training Output

For each model, the trainer will save:
- `{model_name}_best.pt`: Best checkpoint (by validation F1)
- `{model_name}_epoch_{N}.pt`: Checkpoint at epoch N
- `{model_name}_history.json`: Training history with metrics

The training process:
1. Trains for specified number of epochs
2. Validates after each epoch
3. Saves checkpoint if validation F1 improves
4. Early stops if no improvement for `patience` epochs

## Evaluation

### Evaluate Single Model

**Behavioral-Only:**
```bash
python evaluate.py \
  --checkpoint checkpoints/behavioral_baseline_best.pt \
  --model-type behavioral \
  --data-dir data/processed \
  --output-dir results
```

**Cognitive-Enhanced:**
```bash
python evaluate.py \
  --checkpoint checkpoints/cognitive_enhanced_best.pt \
  --model-type cognitive \
  --data-dir data/processed \
  --output-dir results
```

### Compare Both Models

```bash
python evaluate.py \
  --checkpoint checkpoints/cognitive_enhanced_best.pt \
  --model-type cognitive \
  --data-dir data/processed \
  --output-dir results \
  --compare checkpoints/behavioral_baseline_best.pt
```

### Evaluation Output

For each model:
- `{model_name}_results.json`: Precision, Recall, F1, AUC
- `{model_name}_roc.png`: ROC curve visualization
- `{model_name}_confusion.png`: Confusion matrix

For comparison:
- `model_comparison.json`: Side-by-side metrics and improvements

## Model Architecture

### Behavioral-Only Baseline

**Input Representation:**
- **QUERY**: S-BERT embedding of query text (768-dim)
- **CLICK**: S-BERT embedding of first 256 tokens of clicked document (768-dim)
- **SERP_VIEW** (zero-click): Trainable embedding (768-dim)

**Architecture:**
```
Event Embeddings (seq_len, 768)
    ↓
[CLS] Token Prepended
    ↓
Positional Encoding
    ↓
4-Layer Transformer (8 heads, 768 hidden)
    ↓
[CLS] Output (768)
    ↓
Linear Layer (768 → 1)
    ↓
Sigmoid → Abandonment Probability
```

### Cognitive-Enhanced Model

**Input Representation:**
- **Behavioral**: S-BERT embedding (768-dim) - same as baseline
- **Cognitive**: Trainable embedding for cognitive label (32-dim)
- **Combined**: Concatenation (800-dim)

**Architecture:**
```
Event Embeddings (seq_len, 768) + Cognitive Labels (seq_len, 32)
    ↓
Concatenate → (seq_len, 800)
    ↓
[CLS] Token Prepended
    ↓
Positional Encoding
    ↓
4-Layer Transformer (8 heads, 768 hidden)
    ↓
[CLS] Output (768)
    ↓
Linear Layer (768 → 1)
    ↓
Sigmoid → Abandonment Probability
```

## Abandonment Definition

A session is considered **abandoned** if:
1. It has **2 or more query reformulations**
2. It **ends with zero clicks** (last event is not a CLICK)
3. There is **no activity for 30+ minutes** after the last event

This definition captures users who struggle to find relevant information and give up.


## Hardware Requirements

- **GPU Recommended**: CUDA-capable GPU with 8GB+ VRAM for faster training
- **CPU Alternative**: Training possible on CPU but significantly slower (~10-20x)
- **RAM**: 16GB+ recommended for data loading and S-BERT embeddings


S-BERT embedding computation is cached, so subsequent runs are faster.

## Troubleshooting

### Out of Memory

If you encounter OOM errors:
1. Reduce `--batch-size` (try 16 or 8)
2. Reduce `max_seq_len` in dataset.py (default: 50)

### Slow Training

1. Ensure CUDA is properly installed: `python -c "import torch; print(torch.cuda.is_available())"`
2. Use `--device cuda` explicitly
3. Increase `num_workers` in dataloaders (set in dataset.py)

### Poor Performance

1. Check data balance: Verify train/val/test splits have ~50% abandoned sessions
2. Verify cognitive labels: Ensure `cognitive_label` column exists in CSV
3. Check S-BERT model: Ensure embeddings are computed correctly (not all zeros)


