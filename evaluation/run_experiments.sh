#!/bin/bash
# Cross-dataset experiment runner — 4 tasks × 3 datasets = 12 experiments
# Trains behavioral, cognitive, and shuffled models for each combination.
#
# Usage:
#   ./run_experiments.sh                           # Run all 12
#   ./run_experiments.sh --dataset movielens       # Run 4 tasks on MovieLens only
#   ./run_experiments.sh --task session_continuation # Run 1 task on all 3 datasets
#
# Prerequisites:
#   pip install -r requirements.txt datasets
#   Datasets are downloaded from HuggingFace automatically.

set -e
cd "$(dirname "$0")"
ROOT=$(pwd)
export PYTHONUNBUFFERED=1

# Hyperparameters (match paper)
EPOCHS=20
BS=64
LR=5e-5
PATIENCE=7
SEED=42
DEVICE="cuda"  # Change to "cpu" or "mps" if no GPU

# Parse arguments
FILTER_DATASET=""
FILTER_TASK=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dataset) FILTER_DATASET="$2"; shift ;;
        --task) FILTER_TASK="$2"; shift ;;
        --device) DEVICE="$2"; shift ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
    shift
done

# Task definitions: task_name -> preprocessing script
declare -A TASKS=(
    ["session_continuation"]="cross_dataset/data_preprocessing_session_continuation.py"
    ["positive_outcome"]="cross_dataset/data_preprocessing_positive_outcome.py"
    ["explore_exploit"]="cross_dataset/data_preprocessing_explore_exploit.py"
    ["session_success_early"]="cross_dataset/data_preprocessing_session_success_early.py"
)

# Dataset definitions: name -> HuggingFace repo
declare -A DATASETS=(
    ["aol"]="searchsim/cognitive-traces-aol"
    ["stackoverflow"]="searchsim/cognitive-traces-stackoverflow"
    ["movielens"]="searchsim/cognitive-traces-movielens"
)

# Download datasets from HuggingFace if not already cached
download_dataset() {
    local NAME=$1
    local HF_REPO=$2
    local CSV_PATH="data/${NAME}_traces.csv"

    if [ ! -f "$CSV_PATH" ]; then
        echo "  Downloading $NAME from HuggingFace..."
        mkdir -p data
        python3 -c "
from datasets import load_dataset
ds = load_dataset('$HF_REPO')
ds['train'].to_pandas().to_csv('$CSV_PATH', index=False)
print(f'  Saved {len(ds[\"train\"])} rows to $CSV_PATH')
"
    fi
    echo "$CSV_PATH"
}

run_task() {
    local TASK=$1
    local DATASET=$2
    local CSV=$3
    local PREPROC=${TASKS[$TASK]}

    local DATA_DIR="data/processed_${TASK}_${DATASET}"
    local CKPT_DIR="checkpoints/${TASK}_${DATASET}"
    local RES_DIR="results/${TASK}_${DATASET}"

    echo ""
    echo "================================================================"
    echo "  TASK: $TASK ($DATASET)"
    echo "  $(date)"
    echo "================================================================"

    # 1. Preprocess
    echo "[1/3] Preprocessing..."
    if ! python3 "$PREPROC" "$CSV" --output-dir "$DATA_DIR" --seed $SEED > "$RES_DIR/preprocess.log" 2>&1; then
        echo "  FAILED at preprocessing"
        return 1
    fi

    # 2. Train all 3 models
    echo "[2/3] Training (behavioral + cognitive + shuffled)..."
    if ! python3 train.py --data-dir "$DATA_DIR" --output-dir "$CKPT_DIR" \
        --model-type all --num-epochs $EPOCHS --batch-size $BS \
        --learning-rate $LR --patience $PATIENCE --device $DEVICE > "$RES_DIR/train.log" 2>&1; then
        echo "  FAILED at training"
        return 1
    fi

    # 3. Evaluate 3-way comparison
    echo "[3/3] Evaluating..."
    if ! python3 evaluate.py \
        --checkpoint "$CKPT_DIR/cognitive_enhanced_best.pt" \
        --model-type cognitive --data-dir "$DATA_DIR" \
        --output-dir "$RES_DIR" \
        --compare "$CKPT_DIR/behavioral_baseline_best.pt" \
        --shuffled-checkpoint "$CKPT_DIR/shuffled_label_best.pt" \
        --device $DEVICE > "$RES_DIR/evaluate.log" 2>&1; then
        echo "  FAILED at evaluation"
        return 1
    fi

    # Print summary
    if [ -f "$RES_DIR/model_comparison.json" ]; then
        python3 -c "
import json
m = json.load(open('$RES_DIR/model_comparison.json'))
b, c, i = m['behavioral'], m['cognitive'], m['improvements']
print(f'  Behavioral: F1={b[\"f1\"]:.4f}  AUC={b[\"auc\"]:.4f}')
print(f'  Cognitive:  F1={c[\"f1\"]:.4f}  AUC={c[\"auc\"]:.4f}  (Delta_B: {i[\"f1\"]:+.1f}%)')
if 'shuffled' in m:
    s = m['shuffled']
    si = m['shuffled_improvements']
    print(f'  Shuffled:   F1={s[\"f1\"]:.4f}  AUC={s[\"auc\"]:.4f}  (Delta_S: {si[\"f1\"]:+.1f}%)')
"
    fi

    # Cleanup checkpoints and processed data (keep results)
    rm -rf "$CKPT_DIR" "$DATA_DIR"
    echo "  DONE: $TASK ($DATASET)"
}

# Main loop
echo "================================================================"
echo "  CROSS-DATASET EXPERIMENTS — $(date)"
echo "================================================================"

for DATASET in "${!DATASETS[@]}"; do
    [[ -n "$FILTER_DATASET" && "$DATASET" != "$FILTER_DATASET" ]] && continue

    CSV=$(download_dataset "$DATASET" "${DATASETS[$DATASET]}")

    for TASK in "${!TASKS[@]}"; do
        [[ -n "$FILTER_TASK" && "$TASK" != "$FILTER_TASK" ]] && continue

        mkdir -p "results/${TASK}_${DATASET}"
        run_task "$TASK" "$DATASET" "$CSV" || true
    done
done

echo ""
echo "================================================================"
echo "  ALL EXPERIMENTS COMPLETE — $(date)"
echo "================================================================"
