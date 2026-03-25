"""
Step 1: Convert TIP dataset (Pascal VOC XML format) to class-sorted folder structure.

For each split (train / valid / test):
  - Scan dataset/tip/<split>/ for .jpg files
  - Find the matching .xml file (same stem)
  - Parse <object><name> tags to extract class labels
  - Normalise the label to one of: PET, HDPE, LDPE, PP, PS, OTHER
  - Copy the image to dataset/tip_sorted/<split>/<class>/tip_<original_filename>

Run: python step1_convert_tip.py
"""

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
SRC_ROOT   = BASE_DIR / "dataset" / "tip"
DST_ROOT   = BASE_DIR / "dataset" / "tip_sorted"
SPLITS     = ["train", "valid", "test"]
TARGET_CLASSES = {"PET", "HDPE", "LDPE", "PP", "PS", "OTHER"}

# ── class normalisation map ────────────────────────────────────────────────────
RAW_TO_CLASS: dict[str, str] = {
    # PET
    "pet":                            "PET",
    "pete":                           "PET",
    "polyethylene terephthalate":     "PET",
    # HDPE
    "hdpe":                           "HDPE",
    "pe-hd":                          "HDPE",
    "high density polyethylene":      "HDPE",
    # LDPE
    "ldpe":                           "LDPE",
    "pe-ld":                          "LDPE",
    "low density polyethylene":       "LDPE",
    # PP
    "pp":                             "PP",
    "polypropylene":                  "PP",
    # PS
    "ps":                             "PS",
    "polystyrene":                    "PS",
}


def normalise_class(raw: str) -> str:
    """Return one of the six target class names, or 'OTHER'."""
    return RAW_TO_CLASS.get(raw.strip().lower(), "OTHER")


def extract_class_from_xml(xml_path: Path) -> str | None:
    """Return the normalised class name from the first <object><name> in the XML.

    Returns None on any parse error or if no <object> tag is present.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        obj = root.find("object")
        if obj is None:
            print(f"  [WARN] No <object> tag in {xml_path.name} — skipping")
            return None
        name_tag = obj.find("name")
        if name_tag is None or not name_tag.text:
            print(f"  [WARN] Empty <name> tag in {xml_path.name} — skipping")
            return None
        return normalise_class(name_tag.text)
    except ET.ParseError as exc:
        print(f"  [WARN] Malformed XML {xml_path.name}: {exc} — skipping")
        return None


def process_split(split: str) -> dict[str, int]:
    """Process one data split.  Returns per-class image counts."""
    src_dir = SRC_ROOT / split
    counts: dict[str, int] = defaultdict(int)
    skipped = 0

    if not src_dir.is_dir():
        print(f"  [WARN] Source directory not found: {src_dir}")
        return counts

    jpg_files = sorted(src_dir.glob("*.jpg"))
    print(f"\n  Found {len(jpg_files)} JPG files in {src_dir}")

    for jpg_path in jpg_files:
        xml_path = jpg_path.with_suffix(".xml")

        if not xml_path.exists():
            print(f"  [WARN] No matching XML for {jpg_path.name} — skipping")
            skipped += 1
            continue

        cls = extract_class_from_xml(xml_path)
        if cls is None:
            skipped += 1
            continue

        dst_dir = DST_ROOT / split / cls
        dst_dir.mkdir(parents=True, exist_ok=True)

        dst_name = f"tip_{jpg_path.name}"
        dst_path = dst_dir / dst_name

        shutil.copy2(jpg_path, dst_path)
        counts[cls] += 1

    if skipped:
        print(f"  Skipped {skipped} file(s) in split '{split}'")

    return dict(counts)


def main() -> None:
    print("=" * 60)
    print("Step 1 — TIP Dataset Conversion")
    print("=" * 60)

    grand_total = 0
    all_counts: dict[str, dict[str, int]] = {}

    for split in SPLITS:
        print(f"\n[{split.upper()}]")
        counts = process_split(split)
        all_counts[split] = counts
        total = sum(counts.values())
        grand_total += total

        for cls in sorted(TARGET_CLASSES):
            print(f"  {cls:6s}: {counts.get(cls, 0):5d}")
        print(f"  {'TOTAL':6s}: {total:5d}")

    print("\n" + "=" * 60)
    print(f"Grand total images copied: {grand_total}")
    print(f"Output root: {DST_ROOT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
