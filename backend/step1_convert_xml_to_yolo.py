"""
STEP 1: PASCAL VOC XML -> YOLO Format Converter
================================================
Converts bounding box annotations from PASCAL VOC XML format
to YOLO format (class_id cx cy w h) with values normalized to [0, 1].

Input:  dataset/labels/*.xml   (PASCAL VOC format)
Output: dataset/yolo_labels/*.txt (YOLO format)

Class Mapping:
  "mix PP"    -> 0 (PP - Polypropylene)
  "mix HD"    -> 1 (HDPE - High-Density Polyethylene)
  "mix PET"   -> 2 (PET - Polyethylene Terephthalate)
  "mix rigid" -> 3 (Rigid - Rigid plastics)
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

# Resolve paths relative to this script's parent (project root)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Dataset paths
XML_DIR = PROJECT_ROOT / "dataset" / "labels"
OUTPUT_DIR = PROJECT_ROOT / "dataset" / "yolo_labels"

# Class mapping: normalize all variants to a canonical label
# Actual class names found in the XML files:
#   'mix PP', 'mix HD', 'mix PET', 'mix hd', 'mix rigid'
CLASS_MAPPING = {
    "mix pp":    0,
    "mixpp":     0,
    "mix_pp":    0,
    "pp":        0,
    "mix hd":    1,
    "mixhd":     1,
    "mix_hd":    1,
    "hdpe":      1,
    "hd":        1,
    "mix pet":   2,
    "mixpet":    2,
    "mix_pet":   2,
    "pet":       2,
    "mix rigid": 3,
    "mixrigid":  3,
    "mix_rigid": 3,
    "rigid":     3,
}

CLASS_NAMES = {0: "PP", 1: "HDPE", 2: "PET", 3: "Rigid"}


# ──────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────────

def normalize_class_name(raw_name):
    """Normalize a class name: lowercase, strip whitespace, collapse spaces."""
    return " ".join(raw_name.lower().strip().split())


def get_class_id(raw_name):
    """
    Map a raw class name from the XML to a YOLO class ID.
    Returns None if the class name is not recognized.
    """
    normalized = normalize_class_name(raw_name)
    return CLASS_MAPPING.get(normalized, None)


def parse_voc_xml(xml_path):
    """
    Parse a PASCAL VOC XML annotation file.

    Returns a dict with:
        - filename: original image filename
        - width, height: image dimensions
        - objects: list of dicts with (class_name, xmin, ymin, xmax, ymax)

    Returns None if the file cannot be parsed.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"  [ERROR] Failed to parse XML: {xml_path} -> {e}")
        return None

    # Get image filename
    filename_el = root.find("filename")
    filename = filename_el.text.strip() if filename_el is not None and filename_el.text else xml_path.stem

    # Get image dimensions from <size> tag
    size_el = root.find("size")
    if size_el is None:
        print(f"  [WARNING] No <size> tag in {xml_path.name}. Skipping.")
        return None

    width_el = size_el.find("width")
    height_el = size_el.find("height")

    if width_el is None or height_el is None:
        print(f"  [WARNING] Missing width/height in {xml_path.name}. Skipping.")
        return None

    try:
        img_width = int(width_el.text)
        img_height = int(height_el.text)
    except (ValueError, TypeError):
        print(f"  [WARNING] Invalid width/height values in {xml_path.name}. Skipping.")
        return None

    if img_width <= 0 or img_height <= 0:
        print(f"  [WARNING] Zero/negative dimensions in {xml_path.name}. Skipping.")
        return None

    # Parse all <object> entries
    objects = []
    for obj in root.findall("object"):
        name_el = obj.find("name")
        if name_el is None or not name_el.text:
            continue

        class_name = name_el.text.strip()

        bndbox = obj.find("bndbox")
        if bndbox is None:
            continue

        try:
            xmin = float(bndbox.find("xmin").text)
            ymin = float(bndbox.find("ymin").text)
            xmax = float(bndbox.find("xmax").text)
            ymax = float(bndbox.find("ymax").text)
        except (AttributeError, ValueError, TypeError):
            print(f"  [WARNING] Invalid bounding box in {xml_path.name} for class '{class_name}'. Skipping object.")
            continue

        # Clamp coordinates to image bounds
        xmin = max(0, min(xmin, img_width))
        ymin = max(0, min(ymin, img_height))
        xmax = max(0, min(xmax, img_width))
        ymax = max(0, min(ymax, img_height))

        # Validate box dimensions
        if xmax <= xmin or ymax <= ymin:
            print(f"  [WARNING] Invalid box (xmax<=xmin or ymax<=ymin) in {xml_path.name}. Skipping object.")
            continue

        objects.append({
            "class_name": class_name,
            "xmin": xmin,
            "ymin": ymin,
            "xmax": xmax,
            "ymax": ymax,
        })

    return {
        "filename": filename,
        "width": img_width,
        "height": img_height,
        "objects": objects,
    }


def voc_to_yolo(xmin, ymin, xmax, ymax, img_width, img_height):
    """
    Convert PASCAL VOC box (xmin, ymin, xmax, ymax) in pixels
    to YOLO format (cx, cy, w, h) normalized to [0, 1].
    """
    cx = ((xmin + xmax) / 2.0) / img_width
    cy = ((ymin + ymax) / 2.0) / img_height
    w = (xmax - xmin) / img_width
    h = (ymax - ymin) / img_height

    # Clamp to [0, 1]
    cx = max(0.0, min(cx, 1.0))
    cy = max(0.0, min(cy, 1.0))
    w = max(0.0, min(w, 1.0))
    h = max(0.0, min(h, 1.0))

    return cx, cy, w, h


# ──────────────────────────────────────────────────────────────
# MAIN CONVERSION PIPELINE
# ──────────────────────────────────────────────────────────────

def convert_all(xml_dir, output_dir):
    """Scan all XML files, convert to YOLO format, save .txt labels."""

    print("=" * 60)
    print("  STEP 1: PASCAL VOC XML -> YOLO Format Converter")
    print("=" * 60)
    print(f"\n  Input directory:  {xml_dir}")
    print(f"  Output directory: {output_dir}\n")

    # Validate input directory
    if not xml_dir.exists():
        print(f"[FATAL] Input directory not found: {xml_dir}")
        print(f"        Make sure the dataset is placed at: {PROJECT_ROOT / 'dataset'}")
        print(f"        Expected structure:")
        print(f"          dataset/")
        print(f"          +-- img/           <- 95 labeled JPEG images")
        print(f"          +-- labels/        <- PASCAL VOC XML annotation files")
        print(f"          +-- additional_images/")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all XML files recursively
    xml_files = sorted(xml_dir.rglob("*.xml"))
    if not xml_files:
        print(f"[FATAL] No XML files found in: {xml_dir}")
        sys.exit(1)

    print(f"  Found {len(xml_files)} XML file(s) to process.\n")
    print("-" * 60)

    # Tracking stats
    total_converted = 0
    total_skipped = 0
    total_objects = 0
    class_distribution = defaultdict(int)
    unknown_classes = defaultdict(int)
    skipped_files = []

    # Process each XML file
    for xml_path in xml_files:
        # Parse the XML
        annotation = parse_voc_xml(xml_path)
        if annotation is None:
            total_skipped += 1
            skipped_files.append((xml_path.name, "Parse error"))
            continue

        if not annotation["objects"]:
            total_skipped += 1
            skipped_files.append((xml_path.name, "No valid objects"))
            continue

        # Convert each object to YOLO format
        yolo_lines = []
        file_has_valid_objects = False

        for obj in annotation["objects"]:
            class_id = get_class_id(obj["class_name"])

            if class_id is None:
                unknown_classes[obj["class_name"]] += 1
                continue

            cx, cy, w, h = voc_to_yolo(
                obj["xmin"], obj["ymin"], obj["xmax"], obj["ymax"],
                annotation["width"], annotation["height"]
            )

            # YOLO format: class_id cx cy w h (6 decimal places)
            yolo_lines.append(f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
            class_distribution[class_id] += 1
            total_objects += 1
            file_has_valid_objects = True

        if not file_has_valid_objects:
            total_skipped += 1
            skipped_files.append((xml_path.name, "No recognized classes"))
            continue

        # Determine output path (mirror subfolder structure)
        relative_path = xml_path.relative_to(xml_dir)
        output_file = output_dir / relative_path.with_suffix(".txt")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write YOLO label file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(yolo_lines) + "\n")

        total_converted += 1
        print(f"  [OK] {xml_path.name} -> {output_file.name}  ({len(yolo_lines)} objects)")

    # ──────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────

    print("\n" + "=" * 60)
    print("  CONVERSION SUMMARY")
    print("=" * 60)
    print(f"\n  Total XML files found:    {len(xml_files)}")
    print(f"  Successfully converted:   {total_converted}")
    print(f"  Skipped:                  {total_skipped}")
    print(f"  Total bounding boxes:     {total_objects}")

    print(f"\n  Class Distribution:")
    print(f"  {'Class':<8} {'ID':<5} {'Count':<8} {'Percentage':<10}")
    print(f"  {'-' * 35}")
    for class_id in sorted(class_distribution.keys()):
        count = class_distribution[class_id]
        pct = (count / total_objects * 100) if total_objects > 0 else 0
        name = CLASS_NAMES.get(class_id, "Unknown")
        print(f"  {name:<8} {class_id:<5} {count:<8} {pct:.1f}%")

    if unknown_classes:
        print(f"\n  WARNING - Unknown class names encountered (not mapped):")
        for cls_name, count in sorted(unknown_classes.items(), key=lambda x: -x[1]):
            print(f"    - \"{cls_name}\" x {count}")

    if skipped_files:
        print(f"\n  WARNING - Skipped files:")
        for fname, reason in skipped_files:
            print(f"    - {fname}: {reason}")

    print(f"\n  Output saved to: {output_dir}")
    print("=" * 60)


# ──────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    convert_all(XML_DIR, OUTPUT_DIR)
