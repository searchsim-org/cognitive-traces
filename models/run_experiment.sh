#!/bin/bash
# Full pipeline for session abandonment prediction experiment

set -e  # Exit on error

echo "=========================================="
echo "Session Abandonment Prediction Pipeline"
echo "=========================================="

# Configuration
INPUT_CSV=${1:-"../data/aol_1k_annotated.csv"}
DATA_DIR="data/processed"
CHECKPOINT_DIR="checkpoints"
RESULTS_DIR="results"
NUM_EPOCHS=20
BATCH_SIZE=32
LEARNING_RATE=1e-4
PATIENCE=5
SEED=42

echo ""
echo "Configuration:"
echo "  Input CSV: $INPUT_CSV"
echo "  Data directory: $DATA_DIR"
echo "  Checkpoint directory: $CHECKPOINT_DIR"
echo "  Results directory: $RESULTS_DIR"
echo "  Epochs: $NUM_EPOCHS"
echo "  Batch size: $BATCH_SIZE"
echo "  Learning rate: $LEARNING_RATE"
echo "  Patience: $PATIENCE"
echo "  Random seed: $SEED"
echo ""

# Step 1: Data Preprocessing
echo "=========================================="
echo "Step 1: Data Preprocessing"
echo "=========================================="
python data_preprocessing.py "$INPUT_CSV" \
  --output-dir "$DATA_DIR" \
  --seed $SEED

if [ $? -ne 0 ]; then
  echo "Error: Data preprocessing failed!"
  exit 1
fi

echo ""
echo "✓ Data preprocessing complete"

# Step 2: Train Models
echo ""
echo "=========================================="
echo "Step 2: Training Models"
echo "=========================================="
python train.py \
  --data-dir "$DATA_DIR" \
  --output-dir "$CHECKPOINT_DIR" \
  --model-type both \
  --num-epochs $NUM_EPOCHS \
  --batch-size $BATCH_SIZE \
  --learning-rate $LEARNING_RATE \
  --patience $PATIENCE

if [ $? -ne 0 ]; then
  echo "Error: Training failed!"
  exit 1
fi

echo ""
echo "✓ Training complete"

# Step 3: Evaluation
echo ""
echo "=========================================="
echo "Step 3: Evaluation"
echo "=========================================="
python evaluate.py \
  --checkpoint "$CHECKPOINT_DIR/cognitive_enhanced_best.pt" \
  --model-type cognitive \
  --data-dir "$DATA_DIR" \
  --output-dir "$RESULTS_DIR" \
  --compare "$CHECKPOINT_DIR/behavioral_baseline_best.pt"

if [ $? -ne 0 ]; then
  echo "Error: Evaluation failed!"
  exit 1
fi

echo ""
echo "✓ Evaluation complete"

# Summary
echo ""
echo "=========================================="
echo "Pipeline Complete!"
echo "=========================================="
echo ""
echo "Results saved to:"
echo "  - $CHECKPOINT_DIR/ (model checkpoints)"
echo "  - $RESULTS_DIR/ (evaluation metrics and plots)"
echo ""
echo "Key files:"
echo "  - $RESULTS_DIR/model_comparison.json"
echo "  - $RESULTS_DIR/behavioral_baseline_roc.png"
echo "  - $RESULTS_DIR/cognitive_enhanced_roc.png"
echo ""

