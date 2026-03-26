"""
Convert Pascal VOC XML annotations (from dataset/conveyor/labels/) to YOLO format.

The conveyor dataset has 4 detection classes:
  mix PP, mix hd, mix PET, mix rigid
For detection purposes we map all of them to class 0 ("plastic_item") so that
the YOLO model learns to detect any plastic regardless of type — type
classification is handled separately by EfficientNet.

Outputs:
  backend/dataset/yolo_detect/
    images/train/   ← symlinked / copied images
    images/val/
    labels/train/   ← YOLO .txt labels
    labels/val/
    data.yaml        ← dataset config for ultralytics training

Usage:
  cd backend
  python scripts/convert_voc_to_yolo.py
"""

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
SRC_LABELS  = BACKEND_DIR / "dataset" / "conveyor" / "labels"
SRC_IMAGES  = BACKEND_DIR / "dataset" / "conveyor" / "img"
DST_DIR     = BACKEND_DIR / "dataset" / "yolo_detect"

VAL_SPLIT   = 0.15   # 15% of images → validation set
SEED        = 42

# ── Class map — all VOC class names → single YOLO class 0 ─────────────────────
CLASS_MAP = {
    "mix pp":    0,
    "mix hd":    0,
    "mix pet":   0,
    "mix rigid": 0,
}
YOLO_CLASS_NAMES = ["plastic_item"]


def voc_to_yolo(xml_path: Path) -> list:
    """
    Parse a Pascal VOC XML and return a list of YOLO annotation strings.
    YOLO format: <class> <cx> <cy> <w> <h>  (all values 0–1 normalised)
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find("size")
    img_w = int(size.find("width").text)
    img_h = int(size.find("height").text)

    if img_w == 0 or img_h == 0:
        return []

    lines = []
    for obj in root.findall("object"):
        cls_name = obj.find("name").text.strip().lower()
        cls_id = CLASS_MAP.get(cls_name)
        if cls_id is None:
            print(f"  [WARN] unknown class '{cls_name}' in {xml_path.name} — skipped")
            continue

        bb = obj.find("bndbox")
        xmin = float(bb.find("xmin").text)
        ymin = float(bb.find("ymin").text)
        xmax = float(bb.find("xmax").text)
        ymax = float(bb.find("ymax").text)

        cx = ((xmin + xmax) / 2) / img_w
        cy = ((ymin + ymax) / 2) / img_h
        bw = (xmax - xmin) / img_w
        bh = (ymax - ymin) / img_h

        # Clamp to [0, 1]
        cx = max(0.0, min(1.0, cx))
        cy = max(0.0, min(1.0, cy))
        bw = max(0.0, min(1.0, bw))
        bh = max(0.0, min(1.0, bh))

        lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

    return lines


def find_image(xml_path: Path) -> Path | None:
    """Locate the corresponding image for a given XML label file."""
    tree = ET.parse(xml_path)
    filename = tree.getroot().findtext("filename", default="")
    stem = Path(filename).stem if filename else xml_path.stem

    # Look in src images directory first
    for ext in (".jpeg", ".jpg", ".png"):
        candidate = SRC_IMAGES / (stem + ext)
        if candidate.exists():
            return candidate

    # Also search the full dataset/conveyor tree
    for ext in (".jpeg", ".jpg", ".png"):
        hits = list((BACKEND_DIR / "dataset" / "conveyor").rglob(stem + ext))
        if hits:
            return hits[0]

    return None


def main():
    import random
    random.seed(SEED)

    xml_files = sorted(SRC_LABELS.glob("*.xml"))
    if not xml_files:
        print(f"No XML files found in {SRC_LABELS}")
        return

    print(f"Found {len(xml_files)} XML annotation files")

    # Shuffle and split
    random.shuffle(xml_files)
    n_val = max(1, int(len(xml_files) * VAL_SPLIT))
    val_set  = set(f.stem for f in xml_files[:n_val])
    train_set = set(f.stem for f in xml_files[n_val:])
    print(f"  Train: {len(train_set)}  Val: {len(val_set)}")

    # Create output directories
    for split in ("train", "val"):
        (DST_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (DST_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    converted = 0
    skipped   = 0

    for xml_path in xml_files:
        split = "val" if xml_path.stem in val_set else "train"

        lines = voc_to_yolo(xml_path)
        if not lines:
            skipped += 1
            continue

        img_path = find_image(xml_path)
        if img_path is None:
            print(f"  [WARN] image not found for {xml_path.name} — skipped")
            skipped += 1
            continue

        # Copy image
        dst_img = DST_DIR / "images" / split / img_path.name
        shutil.copy2(img_path, dst_img)

        # Write YOLO label
        dst_lbl = DST_DIR / "labels" / split / (img_path.stem + ".txt")
        dst_lbl.write_text("\n".join(lines) + "\n")

        converted += 1

    print(f"\nConverted: {converted}  Skipped: {skipped}")

    # Write data.yaml
    data_yaml = DST_DIR / "data.yaml"
    data_yaml.write_text(
        f"path: {DST_DIR.as_posix()}\n"
        f"train: images/train\n"
        f"val:   images/val\n"
        f"\nnc: {len(YOLO_CLASS_NAMES)}\n"
        f"names: {YOLO_CLASS_NAMES}\n"
    )
    print(f"\ndata.yaml written to {data_yaml}")
    print("\nNext step — train YOLO detector:")
    print("  pip install ultralytics")
    print("  python scripts/train_yolo.py")


if __name__ == "__main__":
    main()
