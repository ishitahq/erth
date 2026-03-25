"""
Step 2: Convert WaDaBa dataset to class-sorted folder structure.

WaDaBa filenames encode plastic properties directly:
  Format: {4digits}_{aNN}b{NN}c{N}d{N}e{N}f{N}g{N}h{N}_jpg.rf.{hash}.jpg
  Example: 0029_a01b00c2d0e0f0g0h1_jpg.rf.<hash>.jpg

Encoding:
  a00 or a07 = OTHER
  a01        = PET
  a02        = HDPE
  a03        = OTHER  (PVC — mapped to OTHER)
  a04        = LDPE
  a05        = PP
  a06        = PS
  d{0-3}     = deformation level (0=none … 3=high)
  e{0-3}     = dirtiness level  (0=clean … 3=very dirty)

For each split:
  - Scan dataset/wadaba/<split>/ for .jpg files
  - Parse filename with regex to extract a, d, e parameters
  - Copy to dataset/wadaba_sorted/<split>/<class>/wadaba_<filename>

Also saves: wadaba_metadata.csv
  columns: filename, split, class, deformation_level, dirtiness_level

Run: python step2_convert_wadaba.py
"""

import re
import shutil
import csv
from pathlib import Path
from collections import defaultdict

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
SRC_ROOT  = BASE_DIR / "dataset" / "wadaba"
DST_ROOT  = BASE_DIR / "dataset" / "wadaba_sorted"
META_CSV  = BASE_DIR / "wadaba_metadata.csv"
SPLITS    = ["train", "valid", "test"]

TARGET_CLASSES = {"PET", "HDPE", "LDPE", "PP", "PS", "OTHER"}

# ── plastic type mapping (a-parameter, two-digit code → class) ─────────────────
PLASTIC_MAP: dict[str, str] = {
    "00": "OTHER",
    "01": "PET",
    "02": "HDPE",
    "03": "OTHER",   # PVC
    "04": "LDPE",
    "05": "PP",
    "06": "PS",
    "07": "OTHER",
}

# ── regex extracts plastic type (a), deformation (d), dirtiness (e) ───────────
# Matches the parameter block embedded in WaDaBa/Roboflow filenames, e.g.:
#   0029_a01b00c2d0e0f0g0h1_jpg.rf...
#   0004a01b05c2d0e1f0g1h1.jpg  (original pre-Roboflow format)
PARAM_RE = re.compile(r"a(\d{2})b\d+c\d+d(\d)e(\d)")


def parse_filename(name: str) -> tuple[str, int, int] | None:
    """Return (class_name, deformation_level, dirtiness_level) or None if no match."""
    m = PARAM_RE.search(name)
    if not m:
        return None
    a_code = m.group(1)
    d_level = int(m.group(2))
    e_level = int(m.group(3))
    cls = PLASTIC_MAP.get(a_code, "OTHER")
    return cls, d_level, e_level


def process_split(split: str, meta_rows: list) -> dict[str, int]:
    """Process one split; append metadata rows in-place. Returns per-class counts."""
    src_dir = SRC_ROOT / split
    counts: dict[str, int] = defaultdict(int)
    skipped = 0

    if not src_dir.is_dir():
        print(f"  [WARN] Source directory not found: {src_dir}")
        return counts

    jpg_files = sorted(src_dir.glob("*.jpg"))
    print(f"\n  Found {len(jpg_files)} JPG files in {src_dir}")

    for jpg_path in jpg_files:
        result = parse_filename(jpg_path.name)
        if result is None:
            print(f"  [WARN] Cannot parse filename: {jpg_path.name} — skipping")
            skipped += 1
            continue

        cls, d_level, e_level = result

        dst_dir = DST_ROOT / split / cls
        dst_dir.mkdir(parents=True, exist_ok=True)

        dst_name = f"wadaba_{jpg_path.name}"
        dst_path = dst_dir / dst_name
        shutil.copy2(jpg_path, dst_path)

        counts[cls] += 1
        meta_rows.append({
            "filename":          dst_name,
            "split":             split,
            "class":             cls,
            "deformation_level": d_level,
            "dirtiness_level":   e_level,
        })

    if skipped:
        print(f"  Skipped {skipped} file(s) in split '{split}'")

    return dict(counts)


def save_metadata(rows: list) -> None:
    fieldnames = ["filename", "split", "class", "deformation_level", "dirtiness_level"]
    with open(META_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nMetadata CSV saved → {META_CSV}  ({len(rows)} rows)")


def main() -> None:
    print("=" * 60)
    print("Step 2 — WaDaBa Dataset Conversion")
    print("=" * 60)

    meta_rows: list = []
    grand_total = 0

    for split in SPLITS:
        print(f"\n[{split.upper()}]")
        counts = process_split(split, meta_rows)
        total = sum(counts.values())
        grand_total += total

        for cls in sorted(TARGET_CLASSES):
            print(f"  {cls:6s}: {counts.get(cls, 0):5d}")
        print(f"  {'TOTAL':6s}: {total:5d}")

    save_metadata(meta_rows)

    print("\n" + "=" * 60)
    print(f"Grand total images copied: {grand_total}")
    print(f"Output root: {DST_ROOT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
