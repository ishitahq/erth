"""
STEP 4: YOLOv8 Fine-Tuning with Transfer Learning
===================================================
Trains YOLOv8s on the augmented plastic waste dataset using
COCO pretrained weights and GPU acceleration.

Input:  dataset/data.yaml, dataset/split/train/, val/
Output: outputs/train_v1/ (best.pt, results, metrics)
"""

import sys
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    print("[FATAL] ultralytics not installed. Run: pip install ultralytics")
    sys.exit(1)

import torch

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DATA_YAML = PROJECT_ROOT / "dataset" / "data.yaml"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
RUN_NAME = "train_v1"

# Training hyperparameters
MODEL_WEIGHTS = "yolov8s.pt"     # COCO pretrained small model
IMG_SIZE = 640
EPOCHS = 100
BATCH_SIZE = 16
OPTIMIZER = "AdamW"
LR0 = 0.001                     # Initial learning rate
LRF = 0.01                      # Final LR factor (cosine annealing)
PATIENCE = 15                   # Early stopping patience
WORKERS = 4

# Auto-detect device
DEVICE = "0" if torch.cuda.is_available() else "cpu"


def main():
    print("=" * 60)
    print("  STEP 4: YOLOv8 Fine-Tuning with Transfer Learning")
    print("=" * 60)

    # Check GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        gpu_mem = getattr(props, 'total_memory', getattr(props, 'total_mem', 0)) / (1024**3)
        print(f"\n  GPU detected: {gpu_name} ({gpu_mem:.1f} GB)")
        print(f"  CUDA version: {torch.version.cuda}")
    else:
        print("\n  [WARNING] No GPU detected. Training will be slow on CPU.")

    if not DATA_YAML.exists():
        print(f"[FATAL] data.yaml not found: {DATA_YAML}")
        print(f"        Run step2_split_dataset.py first.")
        sys.exit(1)

    print(f"\n  Model:          {MODEL_WEIGHTS}")
    print(f"  Image size:     {IMG_SIZE}")
    print(f"  Epochs:         {EPOCHS}")
    print(f"  Batch size:     {BATCH_SIZE}")
    print(f"  Optimizer:      {OPTIMIZER}")
    print(f"  LR:             {LR0} -> {LR0 * LRF} (cosine)")
    print(f"  Early stopping: {PATIENCE} epochs")
    print(f"  Device:         {DEVICE}")
    print(f"  Data config:    {DATA_YAML}\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load pretrained YOLOv8s
    print(f"  Loading pretrained model: {MODEL_WEIGHTS}...")
    model = YOLO(MODEL_WEIGHTS)

    # Train
    print(f"\n  Starting training...")
    print("-" * 60)

    results = model.train(
        data=str(DATA_YAML),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        optimizer=OPTIMIZER,
        lr0=LR0,
        lrf=LRF,
        patience=PATIENCE,
        device=DEVICE,
        workers=WORKERS,
        project=str(OUTPUT_DIR),
        name=RUN_NAME,
        exist_ok=True,
        pretrained=True,
        # Data augmentation (built-in YOLOv8)
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        flipud=0.2,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
        # Regularization
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        box=7.5,
        cls=0.5,
        save=True,
        save_period=-1,
        plots=True,
        verbose=True,
    )

    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE")
    print("=" * 60)
    best_model = OUTPUT_DIR / RUN_NAME / "weights" / "best.pt"
    print(f"\n  Best model: {best_model}")
    print(f"  Results:    {OUTPUT_DIR / RUN_NAME}")
    print("=" * 60)


if __name__ == "__main__":
    main()
