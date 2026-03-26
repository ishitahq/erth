"""
STEP 3: Offline Augmentation Pipeline
======================================
Generates additional augmented training images + labels using
Albumentations to increase dataset diversity, especially for
underrepresented classes (HDPE).

Input:  dataset/split/train/images/ and labels/
Output: Augmented copies appended to the same train directory

Augmentations applied:
  - Horizontal/Vertical flip
  - Random rotation (+-15 deg)
  - Brightness/contrast jitter
  - Gaussian noise
  - Blur
  - HSV shift
  - Random scale/crop
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path
from collections import Counter

try:
    import albumentations as A
except ImportError:
    print("[FATAL] albumentations not installed. Run: pip install albumentations")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

TRAIN_IMG_DIR = PROJECT_ROOT / "dataset" / "split" / "train" / "images"
TRAIN_LBL_DIR = PROJECT_ROOT / "dataset" / "split" / "train" / "labels"

# How many augmented copies per original image
# More for underrepresented classes
AUGMENTATIONS_PER_IMAGE = {
    0: 3,   # PP (29.5%) - moderate
    1: 8,   # HDPE (9.0%) - heavy augmentation (underrepresented)
    2: 2,   # PET (40.2%) - light
    3: 4,   # Rigid (21.3%) - moderate
}
DEFAULT_AUG_COUNT = 3

CLASS_NAMES = {0: "PP", 1: "HDPE", 2: "PET", 3: "Rigid"}

# Albumentations augmentation pipeline
transform = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.2),
    A.RandomRotate90(p=0.3),
    A.Affine(rotate=(-15, 15), scale=(0.85, 1.15), p=0.5),
    A.OneOf([
        A.GaussianBlur(blur_limit=(3, 5), p=1.0),
        A.MotionBlur(blur_limit=(3, 5), p=1.0),
        A.MedianBlur(blur_limit=3, p=1.0),
    ], p=0.3),
    A.OneOf([
        A.GaussNoise(std_range=(0.01, 0.03), p=1.0),
        A.ISONoise(p=1.0),
    ], p=0.3),
    A.RandomBrightnessContrast(brightness_limit=0.25, contrast_limit=0.25, p=0.5),
    A.HueSaturationValue(hue_shift_limit=15, sat_shift_limit=25, val_shift_limit=20, p=0.4),
    A.CLAHE(clip_limit=2.0, p=0.2),
    A.RandomShadow(p=0.2),
    A.ImageCompression(quality_range=(70, 95), p=0.2),
], bbox_params=A.BboxParams(
    format='yolo',
    label_fields=['class_labels'],
    min_visibility=0.3,
    min_area=100,
))


# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────

def read_yolo_labels(label_path):
    """Read YOLO label file. Returns list of (class_id, cx, cy, w, h)."""
    boxes = []
    classes = []
    with open(label_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 5:
                cls = int(parts[0])
                cx, cy, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                # Clamp to valid YOLO range
                cx = max(0.0, min(cx, 1.0))
                cy = max(0.0, min(cy, 1.0))
                w = max(0.001, min(w, 1.0))
                h = max(0.001, min(h, 1.0))
                boxes.append([cx, cy, w, h])
                classes.append(cls)
    return boxes, classes


def write_yolo_labels(label_path, boxes, classes):
    """Write YOLO label file."""
    with open(label_path, "w") as f:
        for cls, box in zip(classes, boxes):
            cx, cy, w, h = box
            f.write(f"{cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")


def get_dominant_class(classes):
    """Return the most common class in the label."""
    if not classes:
        return -1
    return Counter(classes).most_common(1)[0][0]


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  STEP 3: Offline Augmentation Pipeline")
    print("=" * 60)

    if not TRAIN_IMG_DIR.exists() or not TRAIN_LBL_DIR.exists():
        print(f"[FATAL] Train split not found. Run step2_split_dataset.py first.")
        sys.exit(1)

    # Collect all training image-label pairs
    img_files = sorted([f for f in TRAIN_IMG_DIR.iterdir()
                        if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}
                        and not f.stem.startswith("aug_")])  # Skip already augmented

    print(f"\n  Found {len(img_files)} original training images.")
    print(f"  Augmentation counts per dominant class:")
    for cid, count in sorted(AUGMENTATIONS_PER_IMAGE.items()):
        print(f"    {CLASS_NAMES[cid]:<8} -> {count}x augmentations")

    total_generated = 0
    total_failed = 0
    class_new_counts = Counter()

    for img_path in img_files:
        lbl_path = TRAIN_LBL_DIR / (img_path.stem + ".txt")
        if not lbl_path.exists():
            continue

        # Read image and labels
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"  [WARNING] Cannot read image: {img_path.name}")
            total_failed += 1
            continue

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        boxes, classes = read_yolo_labels(lbl_path)

        if not boxes:
            continue

        dom_class = get_dominant_class(classes)
        aug_count = AUGMENTATIONS_PER_IMAGE.get(dom_class, DEFAULT_AUG_COUNT)

        for i in range(aug_count):
            try:
                result = transform(
                    image=image,
                    bboxes=boxes,
                    class_labels=classes,
                )

                aug_image = result["image"]
                aug_boxes = result["bboxes"]
                aug_classes = result["class_labels"]

                # Skip if all boxes were removed by augmentation
                if not aug_boxes:
                    continue

                # Save augmented image
                aug_stem = f"aug_{img_path.stem}_{i}"
                aug_img_path = TRAIN_IMG_DIR / f"{aug_stem}{img_path.suffix}"
                aug_lbl_path = TRAIN_LBL_DIR / f"{aug_stem}.txt"

                aug_bgr = cv2.cvtColor(aug_image, cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(aug_img_path), aug_bgr)
                write_yolo_labels(aug_lbl_path, aug_boxes, aug_classes)

                total_generated += 1
                for c in aug_classes:
                    class_new_counts[c] += 1

            except Exception as e:
                total_failed += 1

    # ──────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────

    # Count final totals
    final_imgs = len(list(TRAIN_IMG_DIR.glob("*.*")))
    final_lbls = len(list(TRAIN_LBL_DIR.glob("*.txt")))

    print("\n" + "=" * 60)
    print("  AUGMENTATION SUMMARY")
    print("=" * 60)
    print(f"\n  Original training images:   {len(img_files)}")
    print(f"  Augmented images generated: {total_generated}")
    print(f"  Failed:                     {total_failed}")
    print(f"  Final training images:      {final_imgs}")
    print(f"  Final training labels:      {final_lbls}")

    print(f"\n  New bounding boxes added per class:")
    for cid in range(4):
        print(f"    {CLASS_NAMES[cid]:<8} +{class_new_counts.get(cid, 0)}")

    print("=" * 60)


if __name__ == "__main__":
    main()
