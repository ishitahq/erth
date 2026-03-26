"""
STEP 7: Evaluation (mAP, Precision, Recall, Confusion Matrix)
===============================================================
Evaluates the best YOLOv8 model on the test set and generates
performance metrics, plots, and a confusion matrix.

Input:
  outputs/train_v2/weights/best.pt  <- retrained model (or train_v1)
  dataset/split/test/               <- test images + labels
Output:
  outputs/evaluation/               <- metrics, plots, confusion matrix
"""

import sys
import json
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    print("[FATAL] ultralytics not installed.")
    sys.exit(1)

import torch

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Try V2 model first, fall back to V1
V2_MODEL = PROJECT_ROOT / "outputs" / "train_v2" / "weights" / "best.pt"
V1_MODEL = PROJECT_ROOT / "outputs" / "train_v1" / "weights" / "best.pt"

DATA_YAML = PROJECT_ROOT / "dataset" / "data.yaml"
DATA_YAML_EXPANDED = PROJECT_ROOT / "dataset" / "data_expanded.yaml"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "evaluation"

IMG_SIZE = 640
DEVICE = "0" if torch.cuda.is_available() else "cpu"

CLASS_NAMES = {0: "PP", 1: "HDPE", 2: "PET", 3: "Rigid"}


def main():
    print("=" * 60)
    print("  STEP 7: Model Evaluation")
    print("=" * 60)

    # Find best model
    if V2_MODEL.exists():
        model_path = V2_MODEL
        data_yaml = DATA_YAML_EXPANDED if DATA_YAML_EXPANDED.exists() else DATA_YAML
        print(f"\n  Using retrained model (V2): {model_path}")
    elif V1_MODEL.exists():
        model_path = V1_MODEL
        data_yaml = DATA_YAML
        print(f"\n  Using initial model (V1): {model_path}")
    else:
        print(f"[FATAL] No trained model found.")
        print(f"        Run step4_yolo_train.py or step6_retrain.py first.")
        sys.exit(1)

    if not data_yaml.exists():
        print(f"[FATAL] data.yaml not found: {data_yaml}")
        sys.exit(1)

    print(f"  Data config: {data_yaml}")
    print(f"  Device: {DEVICE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load model
    model = YOLO(str(model_path))

    # Run validation on test split
    print(f"\n  Running evaluation on test set...")
    print("-" * 60)

    metrics = model.val(
        data=str(data_yaml),
        split="test",
        imgsz=IMG_SIZE,
        device=DEVICE,
        plots=True,
        save_json=True,
        project=str(OUTPUT_DIR),
        name="test_results",
        exist_ok=True,
        verbose=True,
    )

    # Extract metrics
    print("\n" + "=" * 60)
    print("  EVALUATION RESULTS")
    print("=" * 60)

    # Overall metrics
    map50 = metrics.box.map50
    map50_95 = metrics.box.map
    print(f"\n  Overall Metrics:")
    print(f"    mAP@0.5:      {map50:.4f}")
    print(f"    mAP@0.5:0.95: {map50_95:.4f}")

    # Per-class metrics
    print(f"\n  Per-Class Results:")
    print(f"  {'Class':<8} {'Precision':<12} {'Recall':<12} {'mAP@0.5':<12} {'mAP@0.5:0.95':<14}")
    print(f"  {'-'*56}")

    results_dict = {}
    ap50_per_class = metrics.box.ap50
    ap_per_class = metrics.box.ap
    
    for i in range(len(ap50_per_class)):
        cls_name = CLASS_NAMES.get(i, f"Class_{i}")
        p = float(metrics.box.p[i]) if i < len(metrics.box.p) else 0
        r = float(metrics.box.r[i]) if i < len(metrics.box.r) else 0
        ap50 = float(ap50_per_class[i])
        ap = float(ap_per_class[i])
        print(f"  {cls_name:<8} {p:<12.4f} {r:<12.4f} {ap50:<12.4f} {ap:<14.4f}")
        results_dict[cls_name] = {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "mAP50": round(ap50, 4),
            "mAP50_95": round(ap, 4),
        }

    # Save results to JSON
    full_results = {
        "model": str(model_path),
        "overall": {
            "mAP50": round(float(map50), 4),
            "mAP50_95": round(float(map50_95), 4),
        },
        "per_class": results_dict,
    }

    results_json = OUTPUT_DIR / "test_results" / "metrics.json"
    results_json.parent.mkdir(parents=True, exist_ok=True)
    with open(results_json, "w") as f:
        json.dump(full_results, f, indent=2)

    print(f"\n  Results saved to: {OUTPUT_DIR / 'test_results'}")
    print(f"  Metrics JSON:    {results_json}")
    print(f"  Confusion matrix and plots saved in the same directory.")
    print("=" * 60)


if __name__ == "__main__":
    main()
