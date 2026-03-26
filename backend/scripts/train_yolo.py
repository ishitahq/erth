"""
Train a YOLOv8n detector on the converted conveyor belt dataset.

Requires:
  pip install ultralytics
  python scripts/convert_voc_to_yolo.py   (run this first!)

The trained model checkpoint (best.pt) is automatically copied to
backend/models/plastic_detector.pt so the API can use it immediately.

Usage:
  cd backend
  python scripts/train_yolo.py
"""

import shutil
from pathlib import Path

BACKEND_DIR  = Path(__file__).resolve().parent.parent
DATA_YAML    = BACKEND_DIR / "dataset" / "yolo_detect" / "data.yaml"
OUTPUT_DIR   = BACKEND_DIR / "dataset" / "yolo_detect" / "runs"
MODELS_DIR   = BACKEND_DIR / "models"
DEST_MODEL   = MODELS_DIR / "plastic_detector.pt"


def main():
    if not DATA_YAML.exists():
        print("data.yaml not found. Run convert_voc_to_yolo.py first.")
        return

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics not installed. Run: pip install ultralytics")
        return

    print("Starting YOLOv8n training on plastic_item detector...")
    print(f"  Dataset : {DATA_YAML}")
    print(f"  Output  : {OUTPUT_DIR}")

    model = YOLO("yolov8n.pt")  # pre-trained COCO nano model — fine-tune from here

    results = model.train(
        data=str(DATA_YAML),
        epochs=100,
        imgsz=640,
        batch=8,
        patience=20,              # early stopping
        project=str(OUTPUT_DIR),
        name="plastic_detector",
        exist_ok=True,
        augment=True,             # built-in mosaic, flip, colour jitter
        degrees=15,
        fliplr=0.5,
        flipud=0.1,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        verbose=True,
    )

    best_pt = Path(results.save_dir) / "weights" / "best.pt"
    if best_pt.exists():
        MODELS_DIR.mkdir(exist_ok=True)
        shutil.copy2(best_pt, DEST_MODEL)
        print(f"\nBest model saved to {DEST_MODEL}")
        print("Restart the API server to pick up the new detector.")
    else:
        print(f"\n[WARN] best.pt not found at {best_pt}. Check training output.")


if __name__ == "__main__":
    main()
