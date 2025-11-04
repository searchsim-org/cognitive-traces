#!/usr/bin/env python3
"""
Evaluation script for session abandonment prediction models.

Computes:
- Precision
- Recall
- F1 Score
- AUC (Area Under ROC Curve)
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
from pathlib import Path
import json
import argparse
from typing import Dict, Tuple
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score, roc_curve, confusion_matrix
from tqdm import tqdm
import matplotlib.pyplot as plt

from model import create_behavioral_model, create_cognitive_model
from dataset import create_dataloaders


def compute_metrics(labels: np.ndarray, logits: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    """
    Compute classification metrics.
    
    Args:
        labels: Ground truth labels (N, 1)
        logits: Model predictions (N, 1)
        threshold: Classification threshold (default: 0.5)
        
    Returns:
        Dictionary with precision, recall, f1, and auc
    """
    # Convert logits to probabilities
    probs = torch.sigmoid(torch.from_numpy(logits)).numpy()
    
    # Convert to binary predictions
    preds = (probs >= threshold).astype(int)
    labels = labels.astype(int)
    
    # Compute metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average='binary', zero_division=0
    )
    
    # Compute AUC
    try:
        auc = roc_auc_score(labels, probs)
    except:
        auc = 0.0
    
    return {
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'auc': float(auc)
    }


def evaluate_model(
    model: nn.Module,
    dataloader: DataLoader,
    device: str,
    include_cognitive: bool = False
) -> Tuple[Dict[str, float], np.ndarray, np.ndarray]:
    """
    Evaluate model on a dataset.
    
    Args:
        model: PyTorch model
        dataloader: Data loader
        device: Device to evaluate on
        include_cognitive: Whether model uses cognitive labels
        
    Returns:
        Tuple of (metrics_dict, all_labels, all_logits)
    """
    model.eval()
    
    all_logits = []
    all_labels = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc='Evaluating'):
            # Move to device
            event_embeddings = batch['event_embeddings'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            # Forward pass
            if include_cognitive:
                cognitive_ids = batch['cognitive_label_ids'].to(device)
                logits = model(event_embeddings, cognitive_ids, attention_mask)
            else:
                logits = model(event_embeddings, attention_mask)
            
            # Collect predictions
            all_logits.append(logits.cpu().numpy())
            all_labels.append(labels.cpu().numpy())
    
    # Concatenate results
    all_logits = np.concatenate(all_logits, axis=0)
    all_labels = np.concatenate(all_labels, axis=0)
    
    # Compute metrics
    metrics = compute_metrics(all_labels, all_logits)
    
    return metrics, all_labels, all_logits


def plot_roc_curve(
    labels: np.ndarray,
    logits: np.ndarray,
    output_path: str,
    model_name: str = 'Model'
):
    """Plot ROC curve and save to file."""
    probs = torch.sigmoid(torch.from_numpy(logits)).numpy()
    
    fpr, tpr, _ = roc_curve(labels, probs)
    auc = roc_auc_score(labels, probs)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f'{model_name} (AUC = {auc:.3f})', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k--', label='Random (AUC = 0.500)')
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title(f'ROC Curve - {model_name}', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved ROC curve: {output_path}")


def plot_confusion_matrix(
    labels: np.ndarray,
    logits: np.ndarray,
    output_path: str,
    model_name: str = 'Model',
    threshold: float = 0.5
):
    """Plot confusion matrix and save to file."""
    probs = torch.sigmoid(torch.from_numpy(logits)).numpy()
    preds = (probs >= threshold).astype(int)
    
    cm = confusion_matrix(labels, preds)
    
    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap='Blues')
    plt.title(f'Confusion Matrix - {model_name}', fontsize=14)
    plt.colorbar()
    
    classes = ['Non-Abandoned', 'Abandoned']
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, fontsize=11)
    plt.yticks(tick_marks, classes, fontsize=11)
    
    # Add text annotations
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontsize=14)
    
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved confusion matrix: {output_path}")


def load_checkpoint(checkpoint_path: str, model: nn.Module, device: str):
    """Load model checkpoint."""
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    return checkpoint


def evaluate_behavioral_model(
    checkpoint_path: str,
    data_dir: str,
    output_dir: str = 'models/results',
    batch_size: int = 32,
    device: str = None
):
    """Evaluate behavioral-only model on test set."""
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print("="*60)
    print("EVALUATING BEHAVIORAL-ONLY BASELINE MODEL")
    print("="*60)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\nLoading data...")
    _, _, test_loader, _ = create_dataloaders(
        data_dir=data_dir,
        batch_size=batch_size,
        include_cognitive=False
    )
    
    # Create model
    print("Loading model...")
    model = create_behavioral_model(device=device)
    checkpoint = load_checkpoint(checkpoint_path, model, device)
    
    print(f"Loaded checkpoint from epoch {checkpoint['epoch']}")
    print(f"Validation F1: {checkpoint['metrics']['f1']:.4f}")
    
    # Evaluate
    print("\nEvaluating on test set...")
    metrics, labels, logits = evaluate_model(
        model=model,
        dataloader=test_loader,
        device=device,
        include_cognitive=False
    )
    
    # Print results
    print("\n" + "="*60)
    print("TEST SET RESULTS")
    print("="*60)
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1']:.4f}")
    print(f"AUC:       {metrics['auc']:.4f}")
    
    # Save results
    results_file = output_path / 'behavioral_baseline_results.json'
    with open(results_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\nResults saved: {results_file}")
    
    # Plot ROC curve
    plot_roc_curve(
        labels, logits,
        output_path / 'behavioral_baseline_roc.png',
        model_name='Behavioral-Only Baseline'
    )
    
    # Plot confusion matrix
    plot_confusion_matrix(
        labels, logits,
        output_path / 'behavioral_baseline_confusion.png',
        model_name='Behavioral-Only Baseline'
    )
    
    return metrics


def evaluate_cognitive_model(
    checkpoint_path: str,
    data_dir: str,
    output_dir: str = 'models/results',
    batch_size: int = 32,
    device: str = None
):
    """Evaluate cognitive-enhanced model on test set."""
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print("="*60)
    print("EVALUATING COGNITIVE-ENHANCED MODEL")
    print("="*60)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\nLoading data...")
    _, _, test_loader, num_cognitive_labels = create_dataloaders(
        data_dir=data_dir,
        batch_size=batch_size,
        include_cognitive=True
    )
    
    # Create model
    print("Loading model...")
    model = create_cognitive_model(
        num_cognitive_labels=num_cognitive_labels,
        device=device
    )
    checkpoint = load_checkpoint(checkpoint_path, model, device)
    
    print(f"Loaded checkpoint from epoch {checkpoint['epoch']}")
    print(f"Validation F1: {checkpoint['metrics']['f1']:.4f}")
    
    # Evaluate
    print("\nEvaluating on test set...")
    metrics, labels, logits = evaluate_model(
        model=model,
        dataloader=test_loader,
        device=device,
        include_cognitive=True
    )
    
    # Print results
    print("\n" + "="*60)
    print("TEST SET RESULTS")
    print("="*60)
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1']:.4f}")
    print(f"AUC:       {metrics['auc']:.4f}")
    
    # Save results
    results_file = output_path / 'cognitive_enhanced_results.json'
    with open(results_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\nResults saved: {results_file}")
    
    # Plot ROC curve
    plot_roc_curve(
        labels, logits,
        output_path / 'cognitive_enhanced_roc.png',
        model_name='Cognitive-Enhanced'
    )
    
    # Plot confusion matrix
    plot_confusion_matrix(
        labels, logits,
        output_path / 'cognitive_enhanced_confusion.png',
        model_name='Cognitive-Enhanced'
    )
    
    return metrics


def compare_models(
    behavioral_checkpoint: str,
    cognitive_checkpoint: str,
    data_dir: str,
    output_dir: str = 'models/results',
    batch_size: int = 32,
    device: str = None
):
    """Compare behavioral and cognitive models."""
    print("="*60)
    print("COMPARING MODELS")
    print("="*60)
    
    # Evaluate both models
    print("\n1. Evaluating Behavioral-Only Model...")
    behavioral_metrics = evaluate_behavioral_model(
        behavioral_checkpoint, data_dir, output_dir, batch_size, device
    )
    
    print("\n2. Evaluating Cognitive-Enhanced Model...")
    cognitive_metrics = evaluate_cognitive_model(
        cognitive_checkpoint, data_dir, output_dir, batch_size, device
    )
    
    # Compute improvements
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    
    print(f"\n{'Metric':<15} {'Behavioral':<12} {'Cognitive':<12} {'Improvement':<12}")
    print("-" * 60)
    
    for metric in ['precision', 'recall', 'f1', 'auc']:
        behavioral_val = behavioral_metrics[metric]
        cognitive_val = cognitive_metrics[metric]
        improvement = (cognitive_val - behavioral_val) / behavioral_val * 100
        
        print(f"{metric.capitalize():<15} {behavioral_val:>6.4f}       "
              f"{cognitive_val:>6.4f}       {improvement:>+6.1f}%")
    
    # Save comparison
    comparison = {
        'behavioral': behavioral_metrics,
        'cognitive': cognitive_metrics,
        'improvements': {
            metric: (cognitive_metrics[metric] - behavioral_metrics[metric]) / behavioral_metrics[metric] * 100
            for metric in ['precision', 'recall', 'f1', 'auc']
        }
    }
    
    output_path = Path(output_dir)
    comparison_file = output_path / 'model_comparison.json'
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    print(f"\nComparison saved: {comparison_file}")


def main():
    parser = argparse.ArgumentParser(description='Evaluate session abandonment prediction models')
    parser.add_argument('--checkpoint', type=str, required=True,
                       help='Path to model checkpoint')
    parser.add_argument('--model-type', type=str, choices=['behavioral', 'cognitive'],
                       required=True, help='Type of model to evaluate')
    parser.add_argument('--data-dir', type=str, required=True,
                       help='Directory with preprocessed data')
    parser.add_argument('--output-dir', type=str, default='models/results',
                       help='Output directory for results')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size')
    parser.add_argument('--device', type=str, choices=['cpu', 'cuda'],
                       help='Device to evaluate on (auto-detect if not specified)')
    parser.add_argument('--compare', type=str,
                       help='Path to second checkpoint for comparison')
    
    args = parser.parse_args()
    
    if args.compare:
        # Compare two models
        if args.model_type == 'behavioral':
            compare_models(
                behavioral_checkpoint=args.checkpoint,
                cognitive_checkpoint=args.compare,
                data_dir=args.data_dir,
                output_dir=args.output_dir,
                batch_size=args.batch_size,
                device=args.device
            )
        else:
            compare_models(
                behavioral_checkpoint=args.compare,
                cognitive_checkpoint=args.checkpoint,
                data_dir=args.data_dir,
                output_dir=args.output_dir,
                batch_size=args.batch_size,
                device=args.device
            )
    else:
        # Evaluate single model
        if args.model_type == 'behavioral':
            evaluate_behavioral_model(
                checkpoint_path=args.checkpoint,
                data_dir=args.data_dir,
                output_dir=args.output_dir,
                batch_size=args.batch_size,
                device=args.device
            )
        else:
            evaluate_cognitive_model(
                checkpoint_path=args.checkpoint,
                data_dir=args.data_dir,
                output_dir=args.output_dir,
                batch_size=args.batch_size,
                device=args.device
            )


if __name__ == '__main__':
    main()

