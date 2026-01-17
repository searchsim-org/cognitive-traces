#!/usr/bin/env python3
"""
Training script for session abandonment prediction models.

Supports:
- Behavioral-only baseline
- Cognitive-enhanced model
- Adam optimizer with learning rate 1e-4
- Early stopping based on validation F1 score
- Checkpoint saving
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
from pathlib import Path
import json
import argparse
from typing import Dict, Optional
from tqdm import tqdm
import time

from model import create_behavioral_model, create_cognitive_model
from dataset import create_dataloaders
from evaluate import evaluate_model, compute_metrics


class Trainer:
    """
    Trainer for session abandonment prediction models.
    
    Args:
        model: PyTorch model
        train_loader: Training data loader
        val_loader: Validation data loader
        device: Device to train on
        learning_rate: Learning rate (default: 1e-4)
        output_dir: Directory to save checkpoints
        model_name: Name of the model for logging
    """
    
    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        device: str,
        learning_rate: float = 1e-4,
        output_dir: str = 'models/checkpoints',
        model_name: str = 'model'
    ):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        self.model_name = model_name
        
        # Setup output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Loss function (Binary Cross Entropy with Logits)
        self.criterion = nn.BCEWithLogitsLoss()
        
        # Optimizer (Adam with lr=1e-4)
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # Training state
        self.best_f1 = 0.0
        self.best_epoch = 0
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'val_precision': [],
            'val_recall': [],
            'val_f1': [],
            'val_auc': []
        }
    
    def train_epoch(self) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        pbar = tqdm(self.train_loader, desc='Training')
        for batch in pbar:
            # Move to device
            event_embeddings = batch['event_embeddings'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            
            if 'cognitive_label_ids' in batch:
                # Cognitive-enhanced model
                cognitive_ids = batch['cognitive_label_ids'].to(self.device)
                logits = self.model(event_embeddings, cognitive_ids, attention_mask)
            else:
                # Behavioral-only model
                logits = self.model(event_embeddings, attention_mask)
            
            # Compute loss
            loss = self.criterion(logits, labels)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            # Update stats
            total_loss += loss.item()
            num_batches += 1
            
            pbar.set_postfix({'loss': f'{loss.item():.4f}'})
        
        avg_loss = total_loss / num_batches
        return avg_loss
    
    def validate(self) -> Dict[str, float]:
        """Validate on validation set."""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        all_logits = []
        all_labels = []
        
        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc='Validating'):
                # Move to device
                event_embeddings = batch['event_embeddings'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                if 'cognitive_label_ids' in batch:
                    cognitive_ids = batch['cognitive_label_ids'].to(self.device)
                    logits = self.model(event_embeddings, cognitive_ids, attention_mask)
                else:
                    logits = self.model(event_embeddings, attention_mask)
                
                # Compute loss
                loss = self.criterion(logits, labels)
                total_loss += loss.item()
                num_batches += 1
                
                # Collect predictions
                all_logits.append(logits.cpu().numpy())
                all_labels.append(labels.cpu().numpy())
        
        # Compute metrics
        all_logits = np.concatenate(all_logits, axis=0)
        all_labels = np.concatenate(all_labels, axis=0)
        
        metrics = compute_metrics(all_labels, all_logits)
        metrics['loss'] = total_loss / num_batches
        
        return metrics
    
    def save_checkpoint(self, epoch: int, metrics: Dict[str, float], is_best: bool = False):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'metrics': metrics,
            'history': self.history,
            'best_f1': self.best_f1,
            'best_epoch': self.best_epoch
        }
        
        # Save regular checkpoint
        checkpoint_path = self.output_dir / f'{self.model_name}_epoch_{epoch}.pt'
        torch.save(checkpoint, checkpoint_path)
        print(f"Saved checkpoint: {checkpoint_path}")
        
        # Save best checkpoint
        if is_best:
            best_path = self.output_dir / f'{self.model_name}_best.pt'
            torch.save(checkpoint, best_path)
            print(f"Saved best checkpoint: {best_path}")
    
    def train(self, num_epochs: int = 20, patience: int = 5):
        """
        Train the model.
        
        Args:
            num_epochs: Number of epochs to train
            patience: Early stopping patience (epochs without improvement)
        """
        print(f"\nTraining {self.model_name}...")
        print(f"Device: {self.device}")
        print(f"Epochs: {num_epochs}")
        print(f"Learning rate: {self.optimizer.param_groups[0]['lr']}")
        print(f"Patience: {patience}")
        print("="*60)
        
        epochs_without_improvement = 0
        
        for epoch in range(1, num_epochs + 1):
            print(f"\nEpoch {epoch}/{num_epochs}")
            start_time = time.time()
            
            # Train
            train_loss = self.train_epoch()
            
            # Validate
            val_metrics = self.validate()
            
            # Update history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_metrics['loss'])
            self.history['val_precision'].append(val_metrics['precision'])
            self.history['val_recall'].append(val_metrics['recall'])
            self.history['val_f1'].append(val_metrics['f1'])
            self.history['val_auc'].append(val_metrics['auc'])
            
            # Check if best model
            is_best = val_metrics['f1'] > self.best_f1
            if is_best:
                self.best_f1 = val_metrics['f1']
                self.best_epoch = epoch
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1
            
            # Print metrics
            elapsed = time.time() - start_time
            print(f"\nEpoch {epoch} Summary ({elapsed:.1f}s):")
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss: {val_metrics['loss']:.4f}")
            print(f"  Val Precision: {val_metrics['precision']:.4f}")
            print(f"  Val Recall: {val_metrics['recall']:.4f}")
            print(f"  Val F1: {val_metrics['f1']:.4f} {'⭐ BEST' if is_best else ''}")
            print(f"  Val AUC: {val_metrics['auc']:.4f}")
            
            # Save checkpoint
            self.save_checkpoint(epoch, val_metrics, is_best)
            
            # Early stopping
            if epochs_without_improvement >= patience:
                print(f"\nEarly stopping! No improvement for {patience} epochs.")
                print(f"Best F1: {self.best_f1:.4f} at epoch {self.best_epoch}")
                break
        
        print("\n" + "="*60)
        print(f"Training completed!")
        print(f"Best F1: {self.best_f1:.4f} at epoch {self.best_epoch}")
        print(f"Best checkpoint: {self.output_dir / f'{self.model_name}_best.pt'}")
        
        # Save training history
        history_file = self.output_dir / f'{self.model_name}_history.json'
        with open(history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
        print(f"Training history saved: {history_file}")
        
        return self.best_f1


def train_behavioral_model(
    data_dir: str,
    output_dir: str = 'models/checkpoints',
    num_epochs: int = 20,
    batch_size: int = 32,
    learning_rate: float = 1e-4,
    patience: int = 5,
    device: Optional[str] = None
) -> float:
    """
    Train behavioral-only baseline model.
    
    Returns:
        Best validation F1 score
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print("="*60)
    print("TRAINING BEHAVIORAL-ONLY BASELINE MODEL")
    print("="*60)
    
    # Load data
    train_loader, val_loader, test_loader, _ = create_dataloaders(
        data_dir=data_dir,
        batch_size=batch_size,
        include_cognitive=False
    )
    
    # Create model
    model = create_behavioral_model(device=device)
    print(f"\nModel parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Create trainer
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        device=device,
        learning_rate=learning_rate,
        output_dir=output_dir,
        model_name='behavioral_baseline'
    )
    
    # Train
    best_f1 = trainer.train(num_epochs=num_epochs, patience=patience)
    
    return best_f1


def train_cognitive_model(
    data_dir: str,
    output_dir: str = 'models/checkpoints',
    num_epochs: int = 20,
    batch_size: int = 32,
    learning_rate: float = 1e-4,
    patience: int = 5,
    device: Optional[str] = None
) -> float:
    """
    Train cognitive-enhanced model.
    
    Returns:
        Best validation F1 score
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print("="*60)
    print("TRAINING COGNITIVE-ENHANCED MODEL")
    print("="*60)
    
    # Load data
    train_loader, val_loader, test_loader, num_cognitive_labels = create_dataloaders(
        data_dir=data_dir,
        batch_size=batch_size,
        include_cognitive=True
    )
    
    print(f"\nNumber of cognitive labels: {num_cognitive_labels}")
    
    # Create model
    model = create_cognitive_model(
        num_cognitive_labels=num_cognitive_labels,
        device=device
    )
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Create trainer
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        device=device,
        learning_rate=learning_rate,
        output_dir=output_dir,
        model_name='cognitive_enhanced'
    )
    
    # Train
    best_f1 = trainer.train(num_epochs=num_epochs, patience=patience)
    
    return best_f1


def main():
    parser = argparse.ArgumentParser(description='Train session abandonment prediction models')
    parser.add_argument('--data-dir', type=str, required=True,
                       help='Directory with preprocessed data')
    parser.add_argument('--output-dir', type=str, default='models/checkpoints',
                       help='Output directory for checkpoints')
    parser.add_argument('--model-type', type=str, choices=['behavioral', 'cognitive', 'both'],
                       default='both', help='Which model(s) to train')
    parser.add_argument('--num-epochs', type=int, default=20,
                       help='Number of epochs to train')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size')
    parser.add_argument('--learning-rate', type=float, default=1e-4,
                       help='Learning rate')
    parser.add_argument('--patience', type=int, default=5,
                       help='Early stopping patience')
    parser.add_argument('--device', type=str, choices=['cpu', 'cuda'],
                       help='Device to train on (auto-detect if not specified)')
    
    args = parser.parse_args()
    
    # Train models
    results = {}
    
    if args.model_type in ['behavioral', 'both']:
        behavioral_f1 = train_behavioral_model(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            num_epochs=args.num_epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            patience=args.patience,
            device=args.device
        )
        results['behavioral'] = behavioral_f1
    
    if args.model_type in ['cognitive', 'both']:
        cognitive_f1 = train_cognitive_model(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            num_epochs=args.num_epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            patience=args.patience,
            device=args.device
        )
        results['cognitive'] = cognitive_f1
    
    # Print final results
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    for model_name, f1_score in results.items():
        print(f"{model_name.capitalize()} Model Best F1: {f1_score:.4f}")
    
    if len(results) == 2:
        improvement = (results['cognitive'] - results['behavioral']) / results['behavioral'] * 100
        print(f"\nImprovement: {improvement:+.1f}%")


if __name__ == '__main__':
    main()

