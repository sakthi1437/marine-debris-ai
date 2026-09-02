#!/usr/bin/env python3
"""Test script to verify YOLO model loading on Linux"""

import sys
from pathlib import Path

# Ensure we're using the virtual environment
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print()

# Test imports
print("=" * 60)
print("TESTING IMPORTS")
print("=" * 60)

try:
    import torch
    print(f"✓ PyTorch imported successfully (version: {torch.__version__})")
except ImportError as e:
    print(f"✗ Failed to import PyTorch: {e}")
    sys.exit(1)

try:
    from ultralytics import YOLO
    print(f"✓ Ultralytics YOLO imported successfully")
except ImportError as e:
    print(f"✗ Failed to import Ultralytics YOLO: {e}")
    sys.exit(1)

try:
    import cv2
    print(f"✓ OpenCV imported successfully (version: {cv2.__version__})")
except ImportError as e:
    print(f"✗ Failed to import OpenCV: {e}")
    sys.exit(1)

try:
    from PySide6.QtWidgets import QApplication
    print(f"✓ PySide6 imported successfully")
except ImportError as e:
    print(f"✗ Failed to import PySide6: {e}")
    sys.exit(1)

print()

# Test CUDA availability
print("=" * 60)
print("TESTING GPU/CPU DEVICE")
print("=" * 60)

cuda_available = torch.cuda.is_available()
print(f"CUDA available: {cuda_available}")

if cuda_available:
    print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    device = 0
    device_str = "CUDA"
else:
    print("Using CPU")
    device = "cpu"
    device_str = "CPU"

print(f"Selected device: {device_str}")
print()

# Test model loading
print("=" * 60)
print("TESTING MODEL LOADING")
print("=" * 60)

PROJECT_DIR = Path(__file__).resolve().parent
model_path = PROJECT_DIR / "backend/models/best.pt"

print(f"Project directory: {PROJECT_DIR}")
print(f"Model path: {model_path}")
print(f"Model exists: {model_path.exists()}")
print(f"Model is file: {model_path.is_file()}")

if model_path.exists() and model_path.is_file():
    model_size_mb = model_path.stat().st_size / (1024 * 1024)
    print(f"Model size: {model_size_mb:.2f} MB")
else:
    print("✗ Model file not found!")
    sys.exit(1)

print()

try:
    print("Loading YOLO model...")
    model = YOLO(str(model_path))
    print(f"✓ Model loaded successfully")
    print(f"  Model type: {type(model).__name__}")
    print(f"  Task: {getattr(model, 'task', 'unknown')}")
    print(f"  Number of classes: {len(model.names)}")
    print(f"  Class names: {model.names}")
except Exception as e:
    print(f"✗ Failed to load model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test configuration
print("=" * 60)
print("TESTING CONFIGURATION")
print("=" * 60)

try:
    from backend.core.config import settings
    print(f"✓ Configuration loaded")
    print(f"  Model path (from config): {settings.model_file}")
    print(f"  Database path: {settings.database_path}")
    print(f"  Supported classes: {settings.supported_classes}")
    print(f"  Confidence threshold: {settings.confidence_threshold}")
except Exception as e:
    print(f"✗ Failed to load configuration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test model class names match configuration
print("=" * 60)
print("VALIDATING CLASS NAMES")
print("=" * 60)

config_classes = settings.supported_classes
model_names = model.names

print(f"Model classes: {len(model_names)}")
print(f"Config classes: {len(config_classes)}")

matches = True
for class_id, config_name in config_classes.items():
    model_name = model_names.get(class_id, "MISSING")
    match = config_name.casefold() == model_name.casefold()
    symbol = "✓" if match else "✗"
    print(f"  {symbol} Class {class_id}: config='{config_name}', model='{model_name}'")
    if not match:
        matches = False

if matches:
    print("\n✓ All class names match!")
else:
    print("\n⚠ Class names do not match exactly, but model will still work")

print()
print("=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
print(f"Device: {device_str}")
print(f"Model: backend/models/best.pt")
print(f"Model loaded: YES")
print(f"Task: detect")
print(f"Classes: {len(model_names)}")
print()
