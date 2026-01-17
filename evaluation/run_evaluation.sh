#!/bin/bash
# Experimental Evaluation Script
# Reproduces the results presented in the paper
#
# Usage: ./run_evaluation.sh <path_to_aol_annotated.csv>

set -e

INPUT_CSV=${1:-"../data/aol_10k_annotated.csv"}

# Hyperparameters
NUM_EPOCHS=30
BATCH_SIZE=16
LEARNING_RATE=5e-5
PATIENCE=7
SEED=42

echo "=============================================="
echo "EXPERIMENTAL EVALUATION"
echo "=============================================="
echo "Input data: $INPUT_CSV"
echo ""

# ============================================
# TASK 1: Session Outcome Prediction
# ============================================
echo "=============================================="
echo "TASK 1: SESSION OUTCOME PREDICTION"
echo "=============================================="

echo "Step 1.1: Data Preprocessing..."
python session_outcome/data_preprocessing_session_outcome.py "$INPUT_CSV" \
    --output-dir session_outcome/data \
    --seed $SEED

echo ""
echo "Step 1.2: Training Models..."
python train.py \
    --data-dir session_outcome/data \
    --output-dir session_outcome/checkpoints \
    --model-type both \
    --num-epochs $NUM_EPOCHS \
    --batch-size $BATCH_SIZE \
    --learning-rate $LEARNING_RATE \
    --patience $PATIENCE

echo ""
echo "Step 1.3: Evaluation..."
python evaluate.py \
    --checkpoint session_outcome/checkpoints/cognitive_enhanced_best.pt \
    --model-type cognitive \
    --data-dir session_outcome/data \
    --output-dir session_outcome/results \
    --compare session_outcome/checkpoints/behavioral_baseline_best.pt

# ============================================
# TASK 2: Struggle Recovery Prediction
# ============================================
echo ""
echo "=============================================="
echo "TASK 2: STRUGGLE RECOVERY PREDICTION"
echo "=============================================="

echo "Step 2.1: Data Preprocessing..."
python struggle_recovery/data_preprocessing_struggle_recovery.py "$INPUT_CSV" \
    --output-dir struggle_recovery/data \
    --prefix-ratio 0.4 \
    --seed $SEED

echo ""
echo "Step 2.2: Training Models..."
python train.py \
    --data-dir struggle_recovery/data \
    --output-dir struggle_recovery/checkpoints \
    --model-type both \
    --num-epochs $NUM_EPOCHS \
    --batch-size $BATCH_SIZE \
    --learning-rate $LEARNING_RATE \
    --patience $PATIENCE

echo ""
echo "Step 2.3: Evaluation..."
python evaluate.py \
    --checkpoint struggle_recovery/checkpoints/cognitive_enhanced_best.pt \
    --model-type cognitive \
    --data-dir struggle_recovery/data \
    --output-dir struggle_recovery/results \
    --compare struggle_recovery/checkpoints/behavioral_baseline_best.pt

# ============================================
# SUMMARY
# ============================================
echo ""
echo "=============================================="
echo "RESULTS SUMMARY"
echo "=============================================="

echo ""
echo "TASK 1: SESSION OUTCOME PREDICTION"
echo "----------------------------------"
if [ -f "session_outcome/results/model_comparison.json" ]; then
    cat session_outcome/results/model_comparison.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f\"Behavioral:  P={d['behavioral']['precision']:.2f}, R={d['behavioral']['recall']:.2f}, F1={d['behavioral']['f1']:.2f}, AUC={d['behavioral']['auc']:.2f}\")
print(f\"Cognitive:   P={d['cognitive']['precision']:.2f}, R={d['cognitive']['recall']:.2f}, F1={d['cognitive']['f1']:.2f}, AUC={d['cognitive']['auc']:.2f}\")
print(f\"Improvement: F1 {d['improvements']['f1']:+.1f}%, AUC {d['improvements']['auc']:+.1f}%\")
"
else
    echo "Results not available"
fi

echo ""
echo "TASK 2: STRUGGLE RECOVERY PREDICTION"
echo "------------------------------------"
if [ -f "struggle_recovery/results/model_comparison.json" ]; then
    cat struggle_recovery/results/model_comparison.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f\"Behavioral:  P={d['behavioral']['precision']:.2f}, R={d['behavioral']['recall']:.2f}, F1={d['behavioral']['f1']:.2f}, AUC={d['behavioral']['auc']:.2f}\")
print(f\"Cognitive:   P={d['cognitive']['precision']:.2f}, R={d['cognitive']['recall']:.2f}, F1={d['cognitive']['f1']:.2f}, AUC={d['cognitive']['auc']:.2f}\")
print(f\"Improvement: F1 {d['improvements']['f1']:+.1f}%, AUC {d['improvements']['auc']:+.1f}%\")
"
else
    echo "Results not available"
fi

echo ""
echo "=============================================="
echo "EVALUATION COMPLETE"
echo "=============================================="
