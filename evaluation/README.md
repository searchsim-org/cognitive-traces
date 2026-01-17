# Experimental Evaluation

This folder contains the code and results for the experimental validation presented in the paper.

## Tasks Evaluated

### 1. Session Outcome Prediction (Primary Task)
Predicts whether a search session will end in success or failure using the first 50% of session events.

**Results:**
| Model | Precision | Recall | F1 | AUC |
|-------|-----------|--------|-----|-----|
| Behavioral Baseline | 0.50 | 1.00 | 0.67 | 0.43 |
| Cognitive-Enhanced | **1.00** | **0.82** | **0.90** | **0.92** |

### 2. Struggle Recovery Prediction (General Utility)
For sessions starting in a struggle state, predicts whether the user will recover to success using the first 40% of events.

**Results:**
| Model | Precision | Recall | F1 | AUC |
|-------|-----------|--------|-----|-----|
| Behavioral Baseline | 0.50 | 1.00 | 0.67 | 0.77 |
| Cognitive-Enhanced | **0.89** | **0.69** | **0.78** | **0.83** |

## Directory Structure

```
evaluation/
├── README.md
├── train.py                 # Model training script
├── evaluate.py              # Model evaluation script
├── model.py                 # Transformer model architecture
├── dataset.py               # Dataset loading utilities
├── run_evaluation.sh        # Script to reproduce experiments
│
├── session_outcome/
│   ├── data_preprocessing_session_outcome.py
│   ├── data/                # Processed train/val/test splits
│   └── results/             # Evaluation outputs and plots
│
└── struggle_recovery/
    ├── data_preprocessing_struggle_recovery.py
    ├── data/                # Processed train/val/test splits
    └── results/             # Evaluation outputs and plots
```

## Reproducing Results

### Prerequisites
```bash
pip install torch pandas numpy scikit-learn sentence-transformers tqdm
```

### Run All Experiments
```bash
cd evaluation
./run_evaluation.sh ../data/aol_1k_annotated.csv
```

### Run Individual Tasks

**Session Outcome Prediction:**
```bash
# Preprocess data
python session_outcome/data_preprocessing_session_outcome.py ../data/aol_1k_annotated.csv \
    --output-dir session_outcome/data

# Train models
python train.py --data-dir session_outcome/data \
    --output-dir session_outcome/checkpoints \
    --model-type both --num-epochs 30 --batch-size 16 --learning-rate 5e-5 --patience 7

# Evaluate
python evaluate.py --checkpoint session_outcome/checkpoints/cognitive_enhanced_best.pt \
    --model-type cognitive --data-dir session_outcome/data \
    --output-dir session_outcome/results \
    --compare session_outcome/checkpoints/behavioral_baseline_best.pt
```

**Struggle Recovery Prediction:**
```bash
# Preprocess data
python struggle_recovery/data_preprocessing_struggle_recovery.py ../data/aol_1k_annotated.csv \
    --output-dir struggle_recovery/data --prefix-ratio 0.4

# Train models
python train.py --data-dir struggle_recovery/data \
    --output-dir struggle_recovery/checkpoints \
    --model-type both --num-epochs 30 --batch-size 16 --learning-rate 5e-5 --patience 7

# Evaluate
python evaluate.py --checkpoint struggle_recovery/checkpoints/cognitive_enhanced_best.pt \
    --model-type cognitive --data-dir struggle_recovery/data \
    --output-dir struggle_recovery/results \
    --compare struggle_recovery/checkpoints/behavioral_baseline_best.pt
```

## Key Findings

1. **Behavioral baseline exhibits mode collapse**: Predicts success for nearly all sessions (Recall 1.00, Precision 0.50), indicating S-BERT embeddings alone cannot distinguish successful from struggling sessions.

2. **Cognitive labels provide discriminative signal**: The cognitive-enhanced model achieves +35% F1 improvement for Session Outcome and +17% for Struggle Recovery.

3. **Complementary signals**: Ablation shows cognitive-only model achieves F1=0.74, below the combined model (F1=0.90), confirming semantic and cognitive features are complementary.
