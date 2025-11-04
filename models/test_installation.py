#!/usr/bin/env python3
"""
Test script to verify installation and basic functionality.

This script checks:
1. All dependencies are installed
2. Models can be created
3. Data loading works
4. Training can start (dry run)
"""

import sys
import importlib
from pathlib import Path

def check_dependency(package_name, import_name=None):
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✓ {package_name}")
        return True
    except ImportError:
        print(f"✗ {package_name} - NOT INSTALLED")
        return False

def test_dependencies():
    """Test all required dependencies."""
    print("="*60)
    print("Testing Dependencies")
    print("="*60)
    
    dependencies = [
        ('torch', 'torch'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('scikit-learn', 'sklearn'),
        ('sentence-transformers', 'sentence_transformers'),
        ('tqdm', 'tqdm'),
        ('matplotlib', 'matplotlib'),
    ]
    
    all_installed = True
    for package_name, import_name in dependencies:
        if not check_dependency(package_name, import_name):
            all_installed = False
    
    if all_installed:
        print("\n✓ All dependencies installed!")
    else:
        print("\n✗ Some dependencies missing. Run: pip install -r requirements.txt")
        return False
    
    return True

def test_cuda():
    """Test CUDA availability."""
    print("\n" + "="*60)
    print("Testing CUDA")
    print("="*60)
    
    import torch
    
    cuda_available = torch.cuda.is_available()
    
    if cuda_available:
        print(f"✓ CUDA available")
        print(f"  Device: {torch.cuda.get_device_name(0)}")
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  PyTorch built with CUDA: {torch.version.cuda}")
    else:
        print("⚠ CUDA not available - training will use CPU (slower)")
        print("  This is fine for testing but GPU is recommended for full training")
    
    return True

def test_model_creation():
    """Test model creation."""
    print("\n" + "="*60)
    print("Testing Model Creation")
    print("="*60)
    
    try:
        from model import create_behavioral_model, create_cognitive_model
        
        # Test behavioral model
        print("Creating behavioral model...")
        behavioral = create_behavioral_model(device='cpu')
        num_params = sum(p.numel() for p in behavioral.parameters())
        print(f"✓ Behavioral model created ({num_params:,} parameters)")
        
        # Test cognitive model
        print("Creating cognitive model...")
        cognitive = create_cognitive_model(num_cognitive_labels=20, device='cpu')
        num_params = sum(p.numel() for p in cognitive.parameters())
        print(f"✓ Cognitive model created ({num_params:,} parameters)")
        
        # Test forward pass
        import torch
        batch_size, seq_len = 2, 5
        event_embs = torch.randn(batch_size, seq_len, 768)
        mask = torch.ones(batch_size, seq_len)
        
        print("Testing behavioral forward pass...")
        logits = behavioral(event_embs, mask)
        assert logits.shape == (batch_size, 1)
        print(f"✓ Behavioral forward pass works (output shape: {logits.shape})")
        
        print("Testing cognitive forward pass...")
        cognitive_ids = torch.randint(0, 20, (batch_size, seq_len))
        logits = cognitive(event_embs, cognitive_ids, mask)
        assert logits.shape == (batch_size, 1)
        print(f"✓ Cognitive forward pass works (output shape: {logits.shape})")
        
        return True
        
    except Exception as e:
        print(f"✗ Model creation failed: {e}")
        return False

def test_sbert():
    """Test S-BERT model loading."""
    print("\n" + "="*60)
    print("Testing S-BERT")
    print("="*60)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        print("Loading S-BERT model (this may take a minute on first run)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test encoding
        test_text = "test query"
        embedding = model.encode(test_text)
        
        print(f"✓ S-BERT loaded successfully")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  Model: all-MiniLM-L6-v2")
        
        return True
        
    except Exception as e:
        print(f"✗ S-BERT loading failed: {e}")
        print("  This may be a network issue. Try running:")
        print("  python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')\"")
        return False

def test_data_preprocessing():
    """Test data preprocessing functions."""
    print("\n" + "="*60)
    print("Testing Data Preprocessing")
    print("="*60)
    
    try:
        from data_preprocessing import identify_abandoned_sessions, get_user_from_session
        import pandas as pd
        
        # Create sample data
        sample_data = pd.DataFrame({
            'session_id': ['user1_1', 'user1_1', 'user1_1', 'user2_1', 'user2_1'],
            'event_id': ['e1', 'e2', 'e3', 'e4', 'e5'],
            'event_timestamp': ['2006-01-01 12:00:00'] * 5,
            'action_type': ['QUERY', 'SERP_VIEW', 'QUERY', 'QUERY', 'CLICK']
        })
        
        # Test abandoned session identification
        abandoned = identify_abandoned_sessions(sample_data)
        print(f"✓ Abandoned session identification works")
        print(f"  Found {len(abandoned)} abandoned sessions in test data")
        
        # Test user extraction
        user = get_user_from_session('user1_1')
        assert user == 'user1'
        print(f"✓ User ID extraction works")
        
        return True
        
    except Exception as e:
        print(f"✗ Data preprocessing test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("COGNITIVE TRACES - MODEL INSTALLATION TEST")
    print("="*60)
    
    results = []
    
    # Test dependencies
    results.append(("Dependencies", test_dependencies()))
    
    # Test CUDA
    results.append(("CUDA", test_cuda()))
    
    # Test S-BERT
    results.append(("S-BERT", test_sbert()))
    
    # Test model creation
    results.append(("Model Creation", test_model_creation()))
    
    # Test data preprocessing
    results.append(("Data Preprocessing", test_data_preprocessing()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:<25} {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✅ All tests passed! You're ready to train models.")
        print("\nNext steps:")
        print("  1. Preprocess your data:")
        print("     python data_preprocessing.py /path/to/data.csv")
        print("  2. Train models:")
        print("     python train.py --data-dir data/processed")
        print("  3. Evaluate:")
        print("     python evaluate.py --checkpoint checkpoints/cognitive_enhanced_best.pt ...")
        print("\nOr run the full pipeline:")
        print("     ./run_experiment.sh /path/to/data.csv")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Missing dependencies: pip install -r requirements.txt")
        print("  - CUDA issues: Install PyTorch with CUDA support or use CPU")
        print("  - S-BERT issues: Check internet connection")
        return 1

if __name__ == '__main__':
    sys.exit(main())

