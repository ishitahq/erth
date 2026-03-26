"""
STEP 5: Pseudo-Labeling on Unlabeled Images
=============================================
Uses the trained YOLOv8 model from Step 4 to generate pseudo-labels
on the 415 unlabeled images. Only high-confidence predictions
(>= 0.85) are kept.

Input:
  outputs/train_v1/weights/best.pt    <- trained model
  dataset/additional_images/          <- 415 unlabeled images
Output:
  dataset/pseudo_labeled/images/      <- copied images
  dataset/pseudo_labeled/labels/      <- generated YOLO labels
"""

import sys
import shutil
from pathlib import Path
from collections import Counter

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

MODEL_PATH = PROJECT_ROOT / "outputs" / "train_v1" / "weights" / "best.pt"
UNLABELED_DIR = PROJECT_ROOT / "dataset" / "additional_images"
OUTPUT_IMG_DIR = PROJECT_ROOT / "dataset" / "pseudo_labeled" / "images"
OUTPUT_LBL_DIR = PROJECT_ROOT / "dataset" / "pseudo_labeled" / "labels"

CONFIDENCE_THRESHOLD = 0.85
IMG_SIZE = 640
DEVICE = "0" if torch.cuda.is_available() else "cpu"

CLASS_NAMES = {0: "PP", 1: "HDPE", 2: "PET", 3: "Rigid"}
IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def main():
    print("=" * 60)
    print("  STEP 5: Pseudo-Labeling on Unlabeled Images")
    print("=" * 60)

    if not MODEL_PATH.exists():
        print(f"[FATAL] Trained model not found: {MODEL_PATH}")
        print(f"        Run step4_yolo_train.py first.")
        sys.exit(1)

    if not UNLABELED_DIR.exists():
        print(f"[FATAL] Unlabeled images dir not found: {UNLABELED_DIR}")
        sys.exit(1)

    # Collect all unlabeled images (from subdirectories)
    all_images = []
    for ext in IMG_EXTENSIONS:
        all_images.extend(UNLABELED_DIR.rglob(f"*{ext}"))
        all_images.extend(UNLABELED_DIR.rglob(f"*{ext.upper()}"))
    all_images = sorted(set(all_images))

    print(f"\n  Found {len(all_images)} unlabeled images.")
    print(f"  Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print(f"  Device: {DEVICE}")
    print(f"  Model: {MODEL_PATH}\n")

    # Create output directories
    OUTPUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_LBL_DIR.mkdir(parents=True, exist_ok=True)

    # Load model
    print(f"  Loading model...")
    model = YOLO(str(MODEL_PATH))

    total_labeled = 0
    total_skipped = 0
    total_boxes = 0
    class_counts = Counter()

    print(f"\n  Processing images...")
    print("-" * 60)

    for img_path in all_images:
        # Run inference
        results = model.predict(
            source=str(img_path),
            imgsz=IMG_SIZE,
            conf=CONFIDENCE_THRESHOLD,
            device=DEVICE,
            verbose=False,
        )

        # Extract high-confidence detections
        result = results[0]
        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            total_skipped += 1
            continue

        # Get image dimensions
        img_h, img_w = result.orig_shape

        # Build YOLO label lines
        yolo_lines = []
        for i in range(len(boxes)):
            conf = float(boxes.conf[i])
            cls_id = int(boxes.cls[i])
            if conf < CONFIDENCE_THRESHOLD:
                continue

            # Get xyxy and convert to YOLO format
            x1, y1, x2, y2 = boxes.xyxy[i].tolist()
            cx = ((x1 + x2) / 2.0) / img_w
            cy = ((y1 + y2) / 2.0) / img_h
            w = (x2 - x1) / img_w
            h = (y2 - y1) / img_h

            # Clamp
            cx = max(0.0, min(cx, 1.0))
            cy = max(0.0, min(cy, 1.0))
            w = max(0.001, min(w, 1.0))
            h = max(0.001, min(h, 1.0))

            yolo_lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
            class_counts[cls_id] += 1
            total_boxes += 1

        if not yolo_lines:
            total_skipped += 1
            continue

        # Save image and label
        # Use a unique name to avoid conflicts
        stem = f"pseudo_{img_path.parent.name}_{img_path.stem}"
        dst_img = OUTPUT_IMG_DIR / f"{stem}{img_path.suffix}"
        dst_lbl = OUTPUT_LBL_DIR / f"{stem}.txt"

        shutil.copy2(img_path, dst_img)
        with open(dst_lbl, "w") as f:
            f.write("\n".join(yolo_lines) + "\n")

        total_labeled += 1
        print(f"  [OK] {img_path.name} -> {len(yolo_lines)} detections (conf >= {CONFIDENCE_THRESHOLD})")

    # Summary
    print("\n" + "=" * 60)
    print("  PSEUDO-LABELING SUMMARY")
    print("=" * 60)
    print(f"\n  Total unlabeled images:    {len(all_images)}")
    print(f"  Successfully pseudo-labeled: {total_labeled}")
    print(f"  Skipped (low confidence):    {total_skipped}")
    print(f"  Total pseudo boxes:          {total_boxes}")

    print(f"\n  Pseudo-label class distribution:")
    for cid in range(4):
        count = class_counts.get(cid, 0)
        pct = (count / total_boxes * 100) if total_boxes > 0 else 0
        print(f"    {CLASS_NAMES[cid]:<8} {count:<8} {pct:.1f}%")

    print(f"\n  Pseudo images: {OUTPUT_IMG_DIR}")
    print(f"  Pseudo labels: {OUTPUT_LBL_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
