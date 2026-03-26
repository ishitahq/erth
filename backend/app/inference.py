"""
Core inference logic — extracted from pipeline-inference.ipynb.

Three stages:
  Stage 1: Type classification   — EfficientNet-B3 (PyTorch or ONNX)
  Stage 2: Grade classification  — CLIP zero-shot (A / B / C)
  Stage 3: Volumetric estimation — Depth Anything V2 metric depth
"""

import math
import logging
from typing import Dict, Optional, Tuple

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
from .models import DEVICE, load_clip, load_depth_model, load_efficientnet, load_onnx_session
from .schemas import ClassificationResult, Dimensions, GradeScores

logger = logging.getLogger(__name__)

# ── Preprocessing Transforms ────────────────────────────────────────────────

# Standard val/inference transform (matches notebook infer_transform)
_infer_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMG_MEAN, std=IMG_STD),
])

_norm = transforms.Normalize(mean=IMG_MEAN, std=IMG_STD)

# 8 deterministic TTA views extracted from the Conveyor evaluation cell
_tta_transforms = [
    # 1. Baseline
    transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(), _norm,
    ]),
    # 2. Horizontal flip
    transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(p=1.0),
        transforms.ToTensor(), _norm,
    ]),
    # 3. Vertical flip
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
    # 6. H-flip + 10° rotation
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


# ── Helpers ──────────────────────────────────────────────────────────────────

def _probs_to_result(probs: torch.Tensor) -> Tuple[str, float, Dict[str, float]]:
    """
    Convert a 1D softmax probability tensor → (predicted_class, confidence, all_scores).
    Always returns the class with the highest probability.
    """
    conf_val = probs.max().item()
    pred_idx = probs.argmax().item()
    all_scores = {CLASS_NAMES[i]: round(probs[i].item(), 4) for i in range(NUM_CLASSES)}

    return CLASS_NAMES[pred_idx], round(conf_val, 4), all_scores


# ── Stage 1a: Type Classification — PyTorch ──────────────────────────────────

def classify_type_pytorch(image: Image.Image) -> Tuple[str, float, Dict[str, float]]:
    """Single forward pass through EfficientNet-B3 (PyTorch)."""
    model = load_efficientnet()
    if model is None:
        raise RuntimeError(
            "EfficientNet model not loaded. Place phase3_best.pth in backend/models/"
        )
    tensor = _infer_transform(image.convert("RGB")).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1).squeeze(0)
    return _probs_to_result(probs)


def classify_type_pytorch_tta(image: Image.Image) -> Tuple[str, float, Dict[str, float]]:
    """8-view TTA inference through EfficientNet-B3 (PyTorch)."""
    model = load_efficientnet()
    if model is None:
        raise RuntimeError(
            "EfficientNet model not loaded. Place phase3_best.pth in backend/models/"
        )
    image_rgb = image.convert("RGB")
    probs_sum = torch.zeros(NUM_CLASSES, device=DEVICE)
    with torch.no_grad():
        for tf in _tta_transforms:
            tensor = tf(image_rgb).unsqueeze(0).to(DEVICE)
            probs_sum += torch.softmax(model(tensor), dim=1).squeeze(0)
    avg_probs = probs_sum / len(_tta_transforms)
    return _probs_to_result(avg_probs)


# ── Stage 1b: Type Classification — ONNX ─────────────────────────────────────

def classify_type_onnx(image: Image.Image) -> Tuple[str, float, Dict[str, float]]:
    """Single forward pass through EfficientNet-B3 (ONNX runtime — faster on CPU)."""
    session = load_onnx_session()
    if session is None:
        raise RuntimeError(
            "ONNX model not loaded. Place plastic_classifier.onnx in backend/models/ "
            "and install onnxruntime."
        )
    # Preprocess: same transform as PyTorch, output numpy float32
    tensor = _infer_transform(image.convert("RGB")).unsqueeze(0).numpy()
    input_name = session.get_inputs()[0].name
    logits = session.run(None, {input_name: tensor})[0]  # shape (1, 6)
    # Softmax manually
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs_np = exp / exp.sum(axis=1, keepdims=True)
    probs = torch.tensor(probs_np[0], dtype=torch.float32)
    return _probs_to_result(probs)


# ── Stage 1 Dispatcher ───────────────────────────────────────────────────────

def classify_type(
    image: Image.Image,
    use_tta: bool = False,
    prefer_onnx: bool = True,
) -> Tuple[str, float, Dict[str, float], str]:
    """
    Classify plastic type. Dispatch order:
      If use_tta  → always use PyTorch (TTA not supported in ONNX path)
      If prefer_onnx and ONNX available → use ONNX (faster CPU inference)
      Otherwise → use PyTorch

    Returns: (predicted_class, confidence, all_scores, backend_used)
    """
    if use_tta:
        label, conf, scores = classify_type_pytorch_tta(image)
        return label, conf, scores, "pytorch"

    if prefer_onnx and load_onnx_session() is not None:
        label, conf, scores = classify_type_onnx(image)
        return label, conf, scores, "onnx"

    label, conf, scores = classify_type_pytorch(image)
    return label, conf, scores, "pytorch"


# ── Stage 2: Grade Classification (CLIP Zero-Shot) ───────────────────────────

def classify_grade(image: Image.Image) -> Optional[Dict]:
    """
    Zero-shot recyclability grading via CLIP ViT-B/32.
    Returns {grade, confidence, action, all_scores} or None if CLIP unavailable.
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
    conf = round(confidence.item(), 4)

    return {
        "grade": grade,
        "confidence": conf,
        "action": GRADE_ACTIONS[grade],
        "all_scores": {
            GRADE_LABELS[i]: round(similarity[0][i].item(), 4)
            for i in range(len(GRADE_LABELS))
        },
    }


# ── Stage 3: Volumetric Estimation ───────────────────────────────────────────

def estimate_volume(image: Image.Image) -> Optional[Dict]:
    """
    Volume proxy via Depth Anything V2 metric depth.

    Uses pinhole camera model (60° FOV) + 2 cm thickness assumption.
    Returns {volume_cm3, width_cm, height_cm} or None if unavailable.
    """
    depth_model = load_depth_model()
    if depth_model is None:
        return None

    try:
        import cv2
    except ImportError:
        logger.warning("opencv-python not installed. Volumetric estimation unavailable.")
        return None

    img_rgb = np.array(image.convert("RGB"))
    cv2_img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    h, w = cv2_img.shape[:2]

    with torch.no_grad():
        depth_map = depth_model.infer_image(cv2_img)  # HxW numpy float32, meters

    avg_depth_m = float(depth_map.mean())
    fov_rad = math.radians(CAMERA_FOV_DEGREES)
    px_to_m = (avg_depth_m * 2 * math.tan(fov_rad / 2)) / w

    real_w_cm = w * px_to_m * 100
    real_h_cm = h * px_to_m * 100
    volume_cm3 = real_w_cm * real_h_cm * PLASTIC_THICKNESS_CM

    return {
        "volume_cm3": round(volume_cm3, 1),
        "width_cm":   round(real_w_cm, 1),
        "height_cm":  round(real_h_cm, 1),
    }


# ── Full Pipeline Orchestration ───────────────────────────────────────────────

def run_full_pipeline(
    image: Image.Image,
    use_tta: bool = False,
    prefer_onnx: bool = True,
) -> ClassificationResult:
    """
    Run the complete 3-stage classification pipeline:
      Stage 1 → EfficientNet (PyTorch or ONNX): plastic type + confidence
      Stage 2 → CLIP: recyclability grade (A / B / C)
      Stage 3 → Depth Anything V2: volumetric estimation

    Missing models are skipped gracefully; their output fields are None.
    """
    # ── Stage 1: Type Classification ─────────────────────────────────────────
    plastic_type, type_conf, all_scores, backend = classify_type(
        image, use_tta=use_tta, prefer_onnx=prefer_onnx
    )

    result = ClassificationResult(
        plastic_type=plastic_type,
        type_confidence=type_conf,
        all_class_scores=all_scores,
        backend_used=backend,
        tta_used=use_tta,
    )

    # ── Stage 2: Grade (skipped if type is Unknown) ──────────────────────────
    if plastic_type != "Unknown":
        grade_result = classify_grade(image)
        if grade_result is not None:
            result.grade = grade_result["grade"]
            result.grade_confidence = grade_result["confidence"]
            result.grade_scores = GradeScores(**grade_result["all_scores"])
            result.action = grade_result["action"]
    else:
        result.action = "Flag for human review"

    # ── Stage 3: Volumetric Estimation ───────────────────────────────────────
    vol_result = estimate_volume(image)
    if vol_result is not None:
        result.volume_cm3 = vol_result["volume_cm3"]
        result.dimensions = Dimensions(
            width_cm=vol_result["width_cm"],
            height_cm=vol_result["height_cm"],
        )

    return result
