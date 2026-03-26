"""
Object detection for conveyor belt images.

Priority:
  1. YOLO (ultralytics) — if backend/models/plastic_detector.pt exists
  2. OpenCV contour-based fallback — always available, works on conveyor belt
     images where plastic items contrast against the belt background.

Training the YOLO model:
  Run:  python scripts/convert_voc_to_yolo.py
  Then: python scripts/train_yolo.py
  Then copy the produced best.pt to backend/models/plastic_detector.pt
"""

import logging
import math
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

YOLO_CHECKPOINT = Path(__file__).resolve().parent.parent / "models" / "plastic_detector.pt"

_yolo_model = None


# ── YOLO Loader ───────────────────────────────────────────────────────────────

def load_yolo():
    """Load YOLO model if checkpoint exists and ultralytics is installed."""
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model
    if not YOLO_CHECKPOINT.exists():
        return None
    try:
        from ultralytics import YOLO  # noqa: PLC0415
        _yolo_model = YOLO(str(YOLO_CHECKPOINT))
        logger.info("YOLO detector loaded from %s", YOLO_CHECKPOINT)
        return _yolo_model
    except ImportError:
        logger.warning("ultralytics not installed — YOLO detector unavailable")
        return None
    except Exception as exc:
        logger.warning("Failed to load YOLO detector: %s", exc)
        return None


def detect_with_yolo(image: Image.Image) -> List[Tuple[int, int, int, int, float]]:
    """
    Run YOLO inference on the image.
    Returns list of (x1, y1, x2, y2, confidence).
    """
    model = load_yolo()
    if model is None:
        return []
    try:
        results = model(np.array(image.convert("RGB")), verbose=False)[0]
        boxes = []
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int).tolist()
            conf = float(box.conf[0].cpu().numpy())
            boxes.append((int(x1), int(y1), int(x2), int(y2), conf))
        return boxes
    except Exception as exc:
        logger.warning("YOLO inference failed: %s", exc)
        return []


# ── OpenCV Contour Fallback ───────────────────────────────────────────────────

def detect_with_opencv(
    image: Image.Image,
    min_area_frac: float = 0.003,   # min object size: 0.3% of image area
    max_area_frac: float = 0.85,    # skip near-full-frame blobs (background)
    nms_iou_thresh: float = 0.4,
) -> List[Tuple[int, int, int, int, float]]:
    """
    Fallback detector using Otsu thresholding + contour detection.

    Works best on conveyor belt images where items contrast against the belt.
    Returns list of (x1, y1, x2, y2, confidence).
    The 'confidence' here is a normalized area proxy (0..1).
    """
    try:
        import cv2
    except ImportError:
        logger.warning("opencv-python not available — cannot run fallback detector")
        return []

    img_rgb = np.array(image.convert("RGB"))
    h, w = img_rgb.shape[:2]
    total_px = h * w
    min_area = int(total_px * min_area_frac)
    max_area = int(total_px * max_area_frac)

    # ── Pre-process ──────────────────────────────────────────────────────
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    # Primary: Otsu threshold
    _, binary_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Secondary: adaptive threshold on the original grayscale
    binary_adapt = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5
    )

    # Combine: OR — catches both high-contrast and texture-based edges
    binary = cv2.bitwise_or(binary_otsu, binary_adapt)

    # Conveyor belts are often dark — plastic items brighter; invert if needed
    n_white = int(np.sum(binary == 255))
    if n_white > total_px * 0.55:
        binary = cv2.bitwise_not(binary)

    # Morphological cleanup
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open, iterations=1)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    raw_boxes = []
    pad = 6
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(w, x + bw + pad)
        y2 = min(h, y + bh + pad)
        # Pseudo-confidence: normalised by a "good object" area (~5% of frame)
        conf = min(1.0, area / (total_px * 0.05))
        raw_boxes.append((x1, y1, x2, y2, conf))

    return _nms(raw_boxes, nms_iou_thresh)


# ── Non-Maximum Suppression ───────────────────────────────────────────────────

def _iou(a: Tuple, b: Tuple) -> float:
    ax1, ay1, ax2, ay2 = a[:4]
    bx1, by1, bx2, by2 = b[:4]
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return inter / (area_a + area_b - inter)


def _nms(
    boxes: List[Tuple[int, int, int, int, float]],
    iou_thresh: float,
) -> List[Tuple[int, int, int, int, float]]:
    """Simple greedy NMS; keeps highest-confidence box when IoU > threshold."""
    if not boxes:
        return []
    boxes = sorted(boxes, key=lambda b: b[4], reverse=True)
    kept: List[Tuple[int, int, int, int, float]] = []
    suppressed = [False] * len(boxes)
    for i, box in enumerate(boxes):
        if suppressed[i]:
            continue
        kept.append(box)
        for j in range(i + 1, len(boxes)):
            if not suppressed[j] and _iou(box, boxes[j]) > iou_thresh:
                suppressed[j] = True
    return kept


# ── Public API ────────────────────────────────────────────────────────────────

def detect_objects(
    image: Image.Image,
) -> Tuple[List[Tuple[int, int, int, int, float]], str]:
    """
    Detect plastic items in a conveyor belt image.

    Returns:
        (boxes, method) where boxes is a list of (x1,y1,x2,y2,conf)
        and method is 'yolo' or 'opencv'.
    """
    yolo_boxes = detect_with_yolo(image)
    if yolo_boxes:
        logger.info("YOLO detected %d objects", len(yolo_boxes))
        return yolo_boxes, "yolo"

    cv_boxes = detect_with_opencv(image)
    logger.info("OpenCV contour detector found %d objects", len(cv_boxes))
    return cv_boxes, "opencv"
