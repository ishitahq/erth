"""
Core inference logic — extracted from pipeline-local.ipynb.

Three stages:
  1. Type classification   (EfficientNet-B3)
  2. Grade classification  (CLIP zero-shot)
  3. Volumetric estimation (Depth Anything V2)
"""

import math
import logging

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from .config import (
    CAMERA_FOV_DEGREES,
    CLASS_NAMES,
    CONFIDENCE_THRESHOLD,
    GRADE_ACTIONS,
    GRADE_LABELS,
    IMG_MEAN,
    IMG_SIZE,
    IMG_STD,
    NUM_CLASSES,
    PLASTIC_THICKNESS_CM,
)
from .models import DEVICE, load_clip, load_depth_model, load_efficientnet
from .schemas import ClassificationResult, Dimensions, GradeScores

logger = logging.getLogger(__name__)

# ── Preprocessing Transforms ────────────────────────────────────────────────

# Standard inference transform (matching notebook val_transforms)
_infer_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMG_MEAN, std=IMG_STD),
])

# Normalization for TTA (shared across all TTA views)
_norm = transforms.Normalize(mean=IMG_MEAN, std=IMG_STD)

# 8 deterministic TTA views from the Conveyor Belt evaluation cell
_tta_transforms = [
    # 1. baseline
    transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(), _norm,
    ]),
    # 2. horizontal flip
    transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(p=1.0),
        transforms.ToTensor(), _norm,
    ]),
    # 3. vertical flip
    transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomVerticalFlip(p=1.0),
        transforms.ToTensor(), _norm,
    ]),
    # 4. +15° rotation
    transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomRotation((15, 15)),
        transforms.ToTensor(), _norm,
    ]),
    # 5. −15° rotation
    transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomRotation((-15, -15)),
        transforms.ToTensor(), _norm,
    ]),
    # 6. h-flip + 10° rotation
    transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(p=1.0),
        transforms.RandomRotation((10, 10)),
        transforms.ToTensor(), _norm,
    ]),
    # 7. 20% brighter
    transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ColorJitter(brightness=(1.2, 1.2)),
        transforms.ToTensor(), _norm,
    ]),
    # 8. 25% darker
    transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ColorJitter(brightness=(0.75, 0.75)),
        transforms.ToTensor(), _norm,
    ]),
]


# ── Stage 1: Type Classification ────────────────────────────────────────────

def classify_type(image: Image.Image) -> tuple[str, float]:
    """
    Classify plastic type using EfficientNet-B3 (single forward pass).

    Returns:
        (predicted_class, confidence) — "Unknown" if conf < threshold.
    """
    model = load_efficientnet()
    if model is None:
        raise RuntimeError(
            "EfficientNet model not loaded. "
            "Place phase3_best.pth in backend/checkpoints/"
        )

    tensor = _infer_transform(image.convert("RGB")).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)
        conf, pred_idx = probs.max(dim=1)

    conf_val = conf.item()
    pred_class = CLASS_NAMES[pred_idx.item()]

    if conf_val < CONFIDENCE_THRESHOLD:
        return "Unknown", conf_val

    return pred_class, conf_val


def classify_type_tta(image: Image.Image) -> tuple[str, float]:
    """
    Classify plastic type using Test-Time Augmentation (8 deterministic views).

    Averages softmax probabilities across all views before taking argmax.
    More robust than single-pass, especially for real-world / conveyor images.

    Returns:
        (predicted_class, confidence) — "Unknown" if conf < threshold.
    """
    model = load_efficientnet()
    if model is None:
        raise RuntimeError(
            "EfficientNet model not loaded. "
            "Place phase3_best.pth in backend/checkpoints/"
        )

    image_rgb = image.convert("RGB")
    probs_sum = torch.zeros(NUM_CLASSES, device=DEVICE)

    with torch.no_grad():
        for tf in _tta_transforms:
            tensor = tf(image_rgb).unsqueeze(0).to(DEVICE)
            probs_sum += torch.softmax(model(tensor), dim=1).squeeze(0)

    avg_probs = probs_sum / len(_tta_transforms)
    conf_val = avg_probs.max().item()
    pred_idx = avg_probs.argmax().item()

    if conf_val < CONFIDENCE_THRESHOLD:
        return "Unknown", conf_val

    return CLASS_NAMES[pred_idx], conf_val


# ── Stage 2: Grade Classification (CLIP Zero-Shot) ──────────────────────────

def classify_grade(image: Image.Image) -> dict | None:
    """
    Classify recyclability grade using CLIP zero-shot inference.

    Returns:
        {grade, confidence, action, all_scores} or None if CLIP unavailable.
    """
    clip_result = load_clip()
    if clip_result is None:
        return None

    clip_model, clip_preprocess, text_features = clip_result

    image_input = clip_preprocess(image.convert("RGB")).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        image_features = clip_model.encode_image(image_input)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        confidence, pred_idx = similarity[0].max(dim=-1)

    grade = GRADE_LABELS[pred_idx.item()]
    conf = confidence.item()

    return {
        "grade": grade,
        "confidence": conf,
        "action": GRADE_ACTIONS[grade],
        "all_scores": {
            GRADE_LABELS[i]: similarity[0][i].item()
            for i in range(len(GRADE_LABELS))
        },
    }


# ── Stage 3: Volumetric Estimation ──────────────────────────────────────────

def estimate_volume(image: Image.Image) -> dict | None:
    """
    Estimate volume proxy using Depth Anything V2 metric depth.

    Uses pinhole camera model with assumed 60° FOV and 2cm plastic thickness.

    Returns:
        {volume_cm3, width_cm, height_cm} or None if depth model unavailable.
    """
    depth_model = load_depth_model()
    if depth_model is None:
        return None

    try:
        import cv2
    except ImportError:
        logger.warning("opencv-python not installed. Volumetric estimation unavailable.")
        return None

    # Convert PIL → CV2 BGR
    img_rgb = np.array(image.convert("RGB"))
    cv2_img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    h, w = cv2_img.shape[:2]

    # Get metric depth map
    with torch.no_grad():
        depth_map = depth_model.infer_image(cv2_img)  # HxW numpy in meters

    avg_depth_m = float(depth_map.mean())

    # Pinhole camera approximation
    fov_rad = math.radians(CAMERA_FOV_DEGREES)
    px_to_m = (avg_depth_m * 2 * math.tan(fov_rad / 2)) / w

    # Estimate real-world dimensions (use full image as bounding box)
    real_w_cm = w * px_to_m * 100
    real_h_cm = h * px_to_m * 100

    # Volume proxy
    volume_cm3 = real_w_cm * real_h_cm * PLASTIC_THICKNESS_CM

    return {
        "volume_cm3": round(volume_cm3, 1),
        "width_cm": round(real_w_cm, 1),
        "height_cm": round(real_h_cm, 1),
    }


# ── Full Pipeline Orchestration ─────────────────────────────────────────────

def run_full_pipeline(
    image: Image.Image,
    use_tta: bool = False,
) -> ClassificationResult:
    """
    Run the complete hierarchical classification pipeline:
      Stage 1 → EfficientNet: plastic type
      Stage 2 → CLIP: recyclability grade
      Stage 3 → Depth: volumetric estimation

    Missing models are skipped gracefully (their fields become null).
    """
    # Stage 1 — Type Classification
    if use_tta:
        plastic_type, type_conf = classify_type_tta(image)
    else:
        plastic_type, type_conf = classify_type(image)

    result = ClassificationResult(
        plastic_type=plastic_type,
        type_confidence=round(type_conf, 4),
    )

    # Stage 2 — Grade (skip if type is Unknown)
    if plastic_type != "Unknown":
        grade_result = classify_grade(image)
        if grade_result is not None:
            result.grade = grade_result["grade"]
            result.grade_confidence = round(grade_result["confidence"], 4)
            result.grade_scores = GradeScores(**grade_result["all_scores"])
            result.action = grade_result["action"]
    else:
        result.action = "Flag for human review"

    # Stage 3 — Volumetric Estimation
    vol_result = estimate_volume(image)
    if vol_result is not None:
        result.volume_cm3 = vol_result["volume_cm3"]
        result.dimensions = Dimensions(
            width_cm=vol_result["width_cm"],
            height_cm=vol_result["height_cm"],
        )

    return result
