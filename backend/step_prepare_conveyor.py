"""
Conveyor Crop Extraction + Dataset Preparation
===============================================
Run this ONCE before step4_train.py to inject real-world conveyor belt crops
into the unified training set.

What this does:
  1. Parses every labeled XML in dataset/conveyor/labels/
  2. Crops each bounding box from the corresponding image
  3. Saves the crop into dataset/unified/train/<class>/conv_<img>_<i>.jpg
  4. Recalculates and overwrites class_weights.json based on the new counts

Safety:
  - Only writes to dataset/unified/train/  — never touches test or valid
  - Skips images/XMLs that are already extracted (idempotent — safe to re-run)
  - Never touches dataset/conveyor/ source files

Run: python step_prepare_conveyor.py
"""

import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from PIL import Image
from tqdm import tqdm

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
CONVEYOR_IMG    = BASE_DIR / "dataset" / "conveyor" / "img"
CONVEYOR_LABELS = BASE_DIR / "dataset" / "conveyor" / "labels"
UNIFIED_TRAIN   = BASE_DIR / "dataset" / "unified" / "train"
WEIGHTS_JSON    = BASE_DIR / "class_weights.json"

CLASS_NAMES = sorted(["HDPE", "LDPE", "OTHER", "PET", "PP", "PS"])

CONVEYOR_CLASS_MAP = {
    "mix pp":    "PP",
    "mix hd":    "HDPE",
    "mix hdpe":  "HDPE",
    "mix pet":   "PET",
    "mix rigid": "OTHER",
}

# Minimum crop dimension in pixels — skip degenerate boxes
MIN_CROP_PX = 8


def find_xml(img_path: Path) -> Path | None:
    candidate = CONVEYOR_LABELS / (img_path.stem + ".xml")
    if candidate.exists():
        return candidate
    for xml in CONVEYOR_LABELS.glob("*.xml"):
        if xml.stem.lower() == img_path.stem.lower():
            return xml
    return None


def parse_xml(xml_path: Path) -> list[dict]:
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as e:
        print(f"  [WARN] Malformed XML skipped: {xml_path.name} ({e})")
        return []

    objects = []
    for obj in root.findall("object"):
        raw = (obj.findtext("name") or "").strip().lower()
        cls = CONVEYOR_CLASS_MAP.get(raw)
        if cls is None:
            continue
        bb = obj.find("bndbox")
        if bb is None:
            continue
        try:
            box = (
                int(float(bb.findtext("xmin"))),
                int(float(bb.findtext("ymin"))),
                int(float(bb.findtext("xmax"))),
                int(float(bb.findtext("ymax"))),
            )
        except (TypeError, ValueError):
            continue
        objects.append({"class": cls, "box": box})
    return objects


def extract_crops() -> Counter:
    """Extract all crops and return count of crops written per class."""
    written: Counter = Counter()
    skipped_exist = 0

    img_files = sorted(CONVEYOR_IMG.glob("*.jpg")) + \
                sorted(CONVEYOR_IMG.glob("*.jpeg")) + \
                sorted(CONVEYOR_IMG.glob("*.JPG")) + \
                sorted(CONVEYOR_IMG.glob("*.JPEG"))

    # deduplicate by lowercase stem
    seen: set[str] = set()
    unique: list[Path] = []
    for p in img_files:
        if p.stem.lower() not in seen:
            seen.add(p.stem.lower())
            unique.append(p)

    print(f"Found {len(unique)} labeled conveyor images.")

    for img_path in tqdm(unique, desc="Extracting crops"):
        xml_path = find_xml(img_path)
        if xml_path is None:
            print(f"  [WARN] No XML for {img_path.name}, skipping.")
            continue

        annotations = parse_xml(xml_path)
        if not annotations:
            continue

        try:
            pil_img = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"  [WARN] Cannot open {img_path.name}: {e}")
            continue

        w, h = pil_img.size

        for i, ann in enumerate(annotations):
            cls = ann["class"]
            xmin, ymin, xmax, ymax = ann["box"]

            # Clamp to image bounds
            xmin = max(0, min(xmin, w - 1))
            xmax = max(xmin + 1, min(xmax, w))
            ymin = max(0, min(ymin, h - 1))
            ymax = max(ymin + 1, min(ymax, h))

            # Skip degenerate crops
            if (xmax - xmin) < MIN_CROP_PX or (ymax - ymin) < MIN_CROP_PX:
                continue

            out_dir  = UNIFIED_TRAIN / cls
            out_dir.mkdir(parents=True, exist_ok=True)
            out_name = f"conv_{img_path.stem}_{i:03d}.jpg"
            out_path = out_dir / out_name

            # Idempotent — skip if already written
            if out_path.exists():
                skipped_exist += 1
                continue

            crop = pil_img.crop((xmin, ymin, xmax, ymax))
            crop.save(out_path, quality=95)
            written[cls] += 1

    if skipped_exist:
        print(f"  (skipped {skipped_exist} already-existing crops)")

    return written


def recalculate_weights() -> None:
    """
    Recount all training images per class and rewrite class_weights.json
    using inverse-frequency weighting normalised so the mean weight == 1.
    """
    counts: dict[str, int] = {}
    for cls in CLASS_NAMES:
        cls_dir = UNIFIED_TRAIN / cls
        if cls_dir.exists():
            counts[cls] = len(list(cls_dir.iterdir()))
        else:
            counts[cls] = 0

    total = sum(counts.values())
    n_classes = len(CLASS_NAMES)

    # inv-freq weight: (total / n_classes) / count  →  mean weight = 1
    weights = {
        cls: (total / n_classes) / max(counts[cls], 1)
        for cls in CLASS_NAMES
    }

    WEIGHTS_JSON.write_text(json.dumps(weights, indent=2))

    print("\nUpdated class_weights.json:")
    print(f"  {'Class':<8} {'Count':>8}  {'Weight':>8}")
    print("  " + "-" * 28)
    for cls in CLASS_NAMES:
        print(f"  {cls:<8} {counts[cls]:>8}  {weights[cls]:>8.4f}")
    print(f"\n  Total training images: {total}")


def main() -> None:
    print("=" * 55)
    print("  Conveyor Crop Extraction")
    print("=" * 55)

    written = extract_crops()

    print("\nCrops written this run:")
    if written:
        for cls, n in sorted(written.items()):
            print(f"  {cls}: +{n}")
        print(f"  Total new crops: {sum(written.values())}")
    else:
        print("  None (all already present — dataset is up to date)")

    print("\nRecalculating class weights...")
    recalculate_weights()

    print("\nDone. You can now run: python step4_train.py")


if __name__ == "__main__":
    main()
