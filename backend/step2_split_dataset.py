"""
STEP 2: Stratified Train/Val/Test Split
========================================
Splits the labeled dataset into train (80%), val (10%), test (10%)
with stratified sampling based on the dominant class per image.

Input:
  dataset/img/          <- labeled JPEG images
  dataset/yolo_labels/  <- YOLO .txt label files from Step 1

Output:
  dataset/split/
    train/images/  train/labels/
    val/images/    val/labels/
    test/images/   test/labels/
  dataset/data.yaml     <- YOLOv8 dataset config file
"""

import os
import sys
import shutil
import random
from pathlib import Path
from collections import defaultdict, Counter

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

IMG_DIR = PROJECT_ROOT / "dataset" / "img"
LABEL_DIR = PROJECT_ROOT / "dataset" / "yolo_labels"
SPLIT_DIR = PROJECT_ROOT / "dataset" / "split"
DATA_YAML = PROJECT_ROOT / "dataset" / "data.yaml"

# Split ratios
TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
TEST_RATIO = 0.10

# Reproducibility
RANDOM_SEED = 42

# Class names (must match Step 1 mapping)
CLASS_NAMES = {0: "PP", 1: "HDPE", 2: "PET", 3: "Rigid"}
NUM_CLASSES = 4

# Supported image extensions
IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


# ──────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────────

def get_dominant_class(label_path):
    """
    Read a YOLO label file and return the dominant (most frequent) class.
    Used for stratified splitting so each class is proportionally represented.
    """
    class_counts = Counter()
    try:
        with open(label_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    class_counts[class_id] += 1
    except Exception:
        return -1  # Unknown

    if not class_counts:
        return -1

    # Return the most common class in this image
    return class_counts.most_common(1)[0][0]


def find_matched_pairs(img_dir, label_dir):
    """
    Find all image-label pairs where both files exist.
    Returns list of (image_path, label_path) tuples.
    """
    pairs = []
    skipped = []

    # Index all label files by stem
    label_stems = {}
    for lbl_file in label_dir.glob("*.txt"):
        label_stems[lbl_file.stem] = lbl_file

    # Match images to labels
    for img_file in sorted(img_dir.iterdir()):
        if img_file.suffix.lower() not in IMG_EXTENSIONS:
            continue
        if img_file.stem in label_stems:
            pairs.append((img_file, label_stems[img_file.stem]))
        else:
            skipped.append(img_file.name)

    return pairs, skipped


def stratified_split(pairs, train_ratio, val_ratio, test_ratio, seed):
    """
    Split pairs into train/val/test sets with stratification by dominant class.
    """
    random.seed(seed)

    # Group pairs by dominant class
    class_groups = defaultdict(list)
    for img_path, lbl_path in pairs:
        dom_class = get_dominant_class(lbl_path)
        class_groups[dom_class].append((img_path, lbl_path))

    train_set, val_set, test_set = [], [], []

    for class_id, group in sorted(class_groups.items()):
        random.shuffle(group)
        n = len(group)
        n_val = max(1, round(n * val_ratio))     # At least 1 per class
        n_test = max(1, round(n * test_ratio))    # At least 1 per class
        n_train = n - n_val - n_test

        # Safety: if too few samples, adjust
        if n_train < 1:
            n_train = 1
            n_val = max(0, (n - 1) // 2)
            n_test = n - 1 - n_val

        train_set.extend(group[:n_train])
        val_set.extend(group[n_train:n_train + n_val])
        test_set.extend(group[n_train + n_val:])

    # Shuffle each split
    random.shuffle(train_set)
    random.shuffle(val_set)
    random.shuffle(test_set)

    return train_set, val_set, test_set


def copy_pairs_to_split(pairs, split_dir, split_name):
    """Copy image+label pairs into the split directory."""
    img_dst = split_dir / split_name / "images"
    lbl_dst = split_dir / split_name / "labels"
    img_dst.mkdir(parents=True, exist_ok=True)
    lbl_dst.mkdir(parents=True, exist_ok=True)

    for img_path, lbl_path in pairs:
        shutil.copy2(img_path, img_dst / img_path.name)
        shutil.copy2(lbl_path, lbl_dst / lbl_path.name)


def write_data_yaml(yaml_path, split_dir, class_names, num_classes):
    """Generate a YOLOv8-compatible data.yaml config file."""
    # Use absolute paths for reliability
    train_path = (split_dir / "train" / "images").resolve()
    val_path = (split_dir / "val" / "images").resolve()
    test_path = (split_dir / "test" / "images").resolve()

    content = f"""# YOLOv8 Dataset Configuration
# Auto-generated by step2_split_dataset.py

path: {split_dir.resolve()}
train: {train_path}
val: {val_path}
test: {test_path}

nc: {num_classes}
names: [{', '.join(f"'{class_names[i]}'" for i in range(num_classes))}]
"""
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(content)


def count_class_distribution(pairs):
    """Count total bounding boxes per class across a set of pairs."""
    dist = Counter()
    for _, lbl_path in pairs:
        try:
            with open(lbl_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 5:
                        dist[int(parts[0])] += 1
        except Exception:
            pass
    return dist


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  STEP 2: Stratified Train/Val/Test Split")
    print("=" * 60)

    # Validate inputs
    if not IMG_DIR.exists():
        print(f"[FATAL] Image directory not found: {IMG_DIR}")
        sys.exit(1)
    if not LABEL_DIR.exists():
        print(f"[FATAL] Label directory not found: {LABEL_DIR}")
        print(f"        Run step1_convert_xml_to_yolo.py first.")
        sys.exit(1)

    # Find matched image-label pairs
    print(f"\n  Scanning for matched image-label pairs...")
    pairs, skipped_imgs = find_matched_pairs(IMG_DIR, LABEL_DIR)
    print(f"  Found {len(pairs)} matched pairs.")
    if skipped_imgs:
        print(f"  Skipped {len(skipped_imgs)} images without labels:")
        for s in skipped_imgs[:10]:
            print(f"    - {s}")

    if len(pairs) == 0:
        print("[FATAL] No matched pairs found. Check file names match between img/ and yolo_labels/.")
        sys.exit(1)

    # Clean previous split
    if SPLIT_DIR.exists():
        print(f"\n  Cleaning previous split directory...")
        shutil.rmtree(SPLIT_DIR)

    # Perform stratified split
    print(f"\n  Splitting with ratios: train={TRAIN_RATIO}, val={VAL_RATIO}, test={TEST_RATIO}")
    print(f"  Random seed: {RANDOM_SEED}")
    train_set, val_set, test_set = stratified_split(
        pairs, TRAIN_RATIO, VAL_RATIO, TEST_RATIO, RANDOM_SEED
    )

    # Copy files
    print(f"\n  Copying files to split directories...")
    copy_pairs_to_split(train_set, SPLIT_DIR, "train")
    print(f"    [OK] train: {len(train_set)} pairs")
    copy_pairs_to_split(val_set, SPLIT_DIR, "val")
    print(f"    [OK] val:   {len(val_set)} pairs")
    copy_pairs_to_split(test_set, SPLIT_DIR, "test")
    print(f"    [OK] test:  {len(test_set)} pairs")

    # Generate data.yaml
    write_data_yaml(DATA_YAML, SPLIT_DIR, CLASS_NAMES, NUM_CLASSES)
    print(f"\n  [OK] data.yaml written to: {DATA_YAML}")

    # ──────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────

    print("\n" + "=" * 60)
    print("  SPLIT SUMMARY")
    print("=" * 60)
    print(f"\n  Total matched pairs: {len(pairs)}")
    print(f"  Train: {len(train_set):>3}  ({len(train_set)/len(pairs)*100:.1f}%)")
    print(f"  Val:   {len(val_set):>3}  ({len(val_set)/len(pairs)*100:.1f}%)")
    print(f"  Test:  {len(test_set):>3}  ({len(test_set)/len(pairs)*100:.1f}%)")

    # Class distribution per split
    for split_name, split_data in [("Train", train_set), ("Val", val_set), ("Test", test_set)]:
        dist = count_class_distribution(split_data)
        total = sum(dist.values())
        print(f"\n  {split_name} class distribution ({total} boxes):")
        print(f"    {'Class':<8} {'Count':<8} {'%':<6}")
        print(f"    {'-'*25}")
        for cid in range(NUM_CLASSES):
            count = dist.get(cid, 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"    {CLASS_NAMES[cid]:<8} {count:<8} {pct:.1f}%")

    print(f"\n  Output directory: {SPLIT_DIR}")
    print(f"  Data config:     {DATA_YAML}")
    print("=" * 60)


if __name__ == "__main__":
    main()
