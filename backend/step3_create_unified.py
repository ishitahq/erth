"""
Step 3: Merge TIP-sorted and WaDaBa-sorted datasets into a single unified dataset.

Source trees (produced by steps 1 & 2):
  dataset/tip_sorted/{train,valid,test}/{class}/*.jpg
  dataset/wadaba_sorted/{train,valid,test}/{class}/*.jpg

Output:
  dataset/unified/{train,valid,test}/{class}/*.jpg

Also computes balanced class weights for the training split using scikit-learn
and saves them to class_weights.json.

Run: python step3_create_unified.py
"""

import json
import shutil
from pathlib import Path
from collections import defaultdict

import numpy as np
from sklearn.utils.class_weight import compute_class_weight

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
TIP_ROOT     = BASE_DIR / "dataset" / "tip_sorted"
WADABA_ROOT  = BASE_DIR / "dataset" / "wadaba_sorted"
UNIFIED_ROOT = BASE_DIR / "dataset" / "unified"
WEIGHTS_JSON = BASE_DIR / "class_weights.json"

SPLITS         = ["train", "valid", "test"]
TARGET_CLASSES = sorted(["PET", "HDPE", "LDPE", "PP", "PS", "OTHER"])
# ImageFolder sorts class folders alphabetically, so we use the same order.
# Result: ['HDPE', 'LDPE', 'OTHER', 'PET', 'PP', 'PS']


def copy_split(split: str) -> dict[str, dict[str, int]]:
    """Copy images from both source trees into the unified folder.

    Returns per-source, per-class counts: {'tip': {cls: n}, 'wadaba': {cls: n}}
    """
    tip_counts:    dict[str, int] = defaultdict(int)
    wadaba_counts: dict[str, int] = defaultdict(int)

    for source_root, counts, tag in [
        (TIP_ROOT,    tip_counts,    "tip"),
        (WADABA_ROOT, wadaba_counts, "wadaba"),
    ]:
        src_split = source_root / split
        if not src_split.is_dir():
            print(f"  [WARN] Not found: {src_split}")
            continue

        for cls_dir in src_split.iterdir():
            if not cls_dir.is_dir():
                continue
            cls = cls_dir.name
            dst_dir = UNIFIED_ROOT / split / cls
            dst_dir.mkdir(parents=True, exist_ok=True)

            for img_path in cls_dir.glob("*.jpg"):
                shutil.copy2(img_path, dst_dir / img_path.name)
                counts[cls] += 1

    return {"tip": dict(tip_counts), "wadaba": dict(wadaba_counts)}


def compute_weights(train_dir: Path) -> dict[str, float]:
    """Compute sklearn balanced class weights from the unified train split."""
    labels: list[str] = []
    for cls in TARGET_CLASSES:
        cls_dir = train_dir / cls
        if cls_dir.is_dir():
            n = sum(1 for _ in cls_dir.glob("*.jpg"))
            labels.extend([cls] * n)

    if not labels:
        raise RuntimeError("No training images found in unified/train/")

    classes = np.array(TARGET_CLASSES)
    weights = compute_class_weight("balanced", classes=classes, y=np.array(labels))
    return {cls: float(w) for cls, w in zip(TARGET_CLASSES, weights)}


def main() -> None:
    print("=" * 60)
    print("Step 3 — Create Unified Dataset")
    print("=" * 60)

    grand_total = 0

    for split in SPLITS:
        print(f"\n[{split.upper()}]")
        source_counts = copy_split(split)

        tip_c    = source_counts["tip"]
        wadaba_c = source_counts["wadaba"]

        split_total = 0
        header = f"  {'Class':<8} {'TIP':>6} {'WaDaBa':>8} {'Total':>7}"
        print(header)
        print("  " + "-" * (len(header) - 2))

        for cls in TARGET_CLASSES:
            t = tip_c.get(cls, 0)
            w = wadaba_c.get(cls, 0)
            tot = t + w
            split_total += tot
            print(f"  {cls:<8} {t:>6} {w:>8} {tot:>7}")

        print(f"  {'TOTAL':<8} {sum(tip_c.values()):>6} {sum(wadaba_c.values()):>8} {split_total:>7}")
        grand_total += split_total

    # Compute and save class weights ──────────────────────────────────────────
    print("\nComputing balanced class weights …")
    weights = compute_weights(UNIFIED_ROOT / "train")

    with open(WEIGHTS_JSON, "w") as fh:
        json.dump(weights, fh, indent=2)

    # Report ──────────────────────────────────────────────────────────────────
    print("\nClass weights (balanced):")
    for cls, w in sorted(weights.items(), key=lambda x: -x[1]):
        print(f"  {cls:<8}: {w:.4f}")

    weight_values = list(weights.values())
    ratio = max(weight_values) / min(weight_values)
    most_over  = max(weights, key=lambda k: weights[k])
    most_under = min(weights, key=lambda k: weights[k])
    print(f"\nMost over-weighted (rare)  class: {most_over}  ({weights[most_over]:.4f})")
    print(f"Most under-weighted (common) class: {most_under}  ({weights[most_under]:.4f})")
    print(f"Imbalance ratio: {ratio:.2f}x")

    print("\n" + "=" * 60)
    print(f"Grand total images: {grand_total}")
    print(f"Unified dataset: {UNIFIED_ROOT}")
    print(f"Class weights:   {WEIGHTS_JSON}")
    print("=" * 60)


if __name__ == "__main__":
    main()
