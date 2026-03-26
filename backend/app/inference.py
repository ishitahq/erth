"""
Core inference logic — extracted from pipeline-inference.ipynb.

Three stages:
  Stage 1: Type classification   — EfficientNet-B3 (PyTorch or ONNX)
  Stage 2: Grade classification  — CLIP zero-shot (A / B / C)
  Stage 3: Volumetric estimation — Depth Anything V2 metric depth

Extended detection pipeline:
  detect_and_classify() — detect multiple objects in a conveyor belt image,
  then run all three stages on each detected crop.
"""

import base64
import io
import math
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from .config import (
    CAMERA_FOV_DEGREES,
    CLASS_NAMES,
    CONFIDENCE_THRESHOLD,
    DEPTH_FG_PERCENTILE,
    GRADE_ACTIONS,
    GRADE_LABELS,
    IMG_MEAN,
    IMG_SIZE,
    IMG_STD,
    NUM_CLASSES,
    PLASTIC_THICKNESS_CM,
)
from .models import DEVICE, load_clip, load_depth_model, load_efficientnet, load_onnx_session
from .schemas import ClassificationResult, DetectedObject, DetectionResult, DetectionSummary, Dimensions, GradeScores

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

    # ── Foreground detection ──────────────────────────────────────────────
    # The plastic item is the closest object — pixels in the bottom N% of depth
    # values form a mask of the foreground object.  We derive:
    #   • obj_depth_m : mean depth of the object itself (not the whole scene)
    #   • obj_w_px / obj_h_px : pixel extent of the object's bounding box
    fg_threshold = float(np.percentile(depth_map, DEPTH_FG_PERCENTILE))
    fg_mask = depth_map <= fg_threshold

    fg_rows = np.where(fg_mask.any(axis=1))[0]
    fg_cols = np.where(fg_mask.any(axis=0))[0]

    if len(fg_rows) > 1 and len(fg_cols) > 1:
        obj_h_px = float(fg_rows[-1] - fg_rows[0])
        obj_w_px = float(fg_cols[-1] - fg_cols[0])
        obj_depth_m = float(depth_map[fg_mask].mean())
    else:
        # Fallback: assume object fills centre 60 % of frame
        obj_w_px = w * 0.6
        obj_h_px = h * 0.6
        obj_depth_m = float(np.percentile(depth_map, 20))

    # Guard against zero/tiny depth (sensor noise, very close objects)
    obj_depth_m = max(obj_depth_m, 0.05)

    # ── Pinhole camera → real dimensions ────────────────────────────────
    fov_rad = math.radians(CAMERA_FOV_DEGREES)
    px_to_m = (obj_depth_m * 2 * math.tan(fov_rad / 2)) / w

    real_w_cm = obj_w_px * px_to_m * 100
    real_h_cm = obj_h_px * px_to_m * 100
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


# ── Conveyor Detection Pipeline ───────────────────────────────────────────────

# Colour palette for bounding box rendering (one colour per plastic type)
_BOX_COLORS: Dict[str, Tuple[int, int, int]] = {
    "PET":     (231, 76,  60),
    "HDPE":    (82,  168, 219),
    "LDPE":    (243, 156, 18),
    "PP":      (126, 217, 87),
    "PS":      (155, 89,  182),
    "OTHER":   (149, 165, 166),
    "Unknown": (107, 114, 128),
}

_GRADE_BADGE_COLORS: Dict[str, Tuple[int, int, int]] = {
    "A": (126, 217, 87),
    "B": (245, 158, 11),
    "C": (239, 68,  68),
}


def _draw_detections(
    image: Image.Image,
    objects: List[Dict],
) -> Image.Image:
    """
    Return a copy of *image* with colour-coded bounding boxes and labels.
    Label format: "#<id> <TYPE> <type_conf>% | Grade <grade>"
    """
    from PIL import ImageDraw  # noqa: PLC0415

    out = image.copy().convert("RGB")
    draw = ImageDraw.Draw(out)

    for obj in objects:
        x1, y1, x2, y2 = obj["bbox"]
        ptype = obj["plastic_type"]
        color = _BOX_COLORS.get(ptype, (200, 200, 200))

        # Box outline (3-pixel border)
        for offset in range(3):
            draw.rectangle(
                [x1 - offset, y1 - offset, x2 + offset, y2 + offset],
                outline=color,
            )

        # Label text
        grade = obj.get("grade") or "?"
        conf_pct = int(round(obj["type_confidence"] * 100))
        label = f"#{obj['object_id']} {ptype} {conf_pct}% | {grade}"

        label_len = len(label)
        char_w, char_h = 7, 13
        lx2 = min(out.width, x1 + label_len * char_w + 6)
        ly1 = max(0, y1 - char_h - 4)

        grade_color = _GRADE_BADGE_COLORS.get(grade, color)
        draw.rectangle([x1, ly1, lx2, y1], fill=grade_color)
        draw.text((x1 + 3, ly1 + 1), label, fill=(0, 0, 0))

    return out


def _volume_for_crop(
    x1: int, y1: int, x2: int, y2: int,
    depth_map: np.ndarray,
    full_w: int,
) -> Optional[Dict]:
    """
    Estimate volume for a single detected crop from a pre-computed depth map.

    Accepts the full-frame depth map (already inferred once) and the crop bbox,
    so depth inference is NOT re-run per object.
    """
    crop_depth = depth_map[y1:y2, x1:x2]
    if crop_depth.size == 0:
        return None

    # Fix A: foreground mask — object is the closest pixels in the crop
    fg_threshold = float(np.percentile(crop_depth, DEPTH_FG_PERCENTILE))
    fg_mask = crop_depth <= fg_threshold
    fg_pixel_count = int(fg_mask.sum())

    if fg_pixel_count < 10:
        fg_mask = np.ones_like(crop_depth, dtype=bool)
        fg_pixel_count = crop_depth.size

    obj_depth_m = float(np.median(crop_depth[fg_mask]))
    obj_depth_m = max(obj_depth_m, 0.05)

    # Use full-frame width for correct angular pixel scale
    fov_rad = math.radians(CAMERA_FOV_DEGREES)
    px_to_m = (obj_depth_m * 2 * math.tan(fov_rad / 2)) / full_w

    # Fix B: pixel-count area instead of bounding-box extent
    object_area_m2 = fg_pixel_count * (px_to_m ** 2)
    side_cm = math.sqrt(object_area_m2) * 100
    volume_cm3 = object_area_m2 * 1e4 * PLASTIC_THICKNESS_CM

    return {
        "volume_cm3": round(volume_cm3, 1),
        "width_cm":   round(side_cm, 1),
        "height_cm":  round(side_cm, 1),
    }


def _infer_full_frame_depth(image: Image.Image) -> Optional[np.ndarray]:
    """Run Depth Anything V2 once on the full frame. Returns HxW depth array or None."""
    depth_model = load_depth_model()
    if depth_model is None:
        return None
    try:
        import cv2  # noqa: PLC0415
    except ImportError:
        return None
    cv2_img = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    with torch.no_grad():
        return depth_model.infer_image(cv2_img)


def detect_and_classify(
    image: Image.Image,
    prefer_onnx: bool = True,
) -> DetectionResult:
    """
    Full conveyor-belt pipeline:
      1. Detect all plastic items (YOLO if available, else OpenCV contours)
      2. For every detected bounding box:
         a. Crop the region
         b. Stage 1 — EfficientNet: plastic type + confidence
         c. Stage 2 — CLIP: recyclability grade (A/B/C)
         d. Stage 3 — Depth Anything: per-object volume
      3. Render annotated image with colour-coded boxes
      4. Return DetectionResult with per-object data + summary counts

    If no objects are detected, the full image is treated as a single item
    (fallback to the original single-item pipeline).
    """
    from .detector import detect_objects  # noqa: PLC0415

    boxes, method = detect_objects(image)

    # ── Fallback: treat whole image as one object ────────────────────────
    if not boxes:
        logger.info("No objects detected — treating full image as single item")
        iw, ih = image.size
        boxes = [(0, 0, iw, ih, 1.0)]
        method = "full_image_fallback"

    objects_out: List[Dict] = []

    # ── Run depth inference ONCE on the full frame ───────────────────────
    full_depth_map = _infer_full_frame_depth(image)

    for idx, (x1, y1, x2, y2, det_conf) in enumerate(boxes, start=1):
        crop = image.crop((x1, y1, x2, y2))

        # Stage 1
        label, type_conf, all_scores, _backend = classify_type(
            crop, prefer_onnx=prefer_onnx
        )

        # Stage 2
        grade_result = classify_grade(crop) if label != "Unknown" else None

        # Stage 3 — reuse the pre-computed depth map
        vol_result = (
            _volume_for_crop(x1, y1, x2, y2, full_depth_map, image.width)
            if full_depth_map is not None else None
        )

        obj: Dict = {
            "object_id":             idx,
            "bbox":                  [x1, y1, x2, y2],
            "detection_confidence":  round(det_conf, 4),
            "plastic_type":          label,
            "type_confidence":       round(type_conf, 4),
            "all_class_scores":      all_scores,
        }

        if grade_result:
            obj["grade"]            = grade_result["grade"]
            obj["grade_confidence"] = round(grade_result["confidence"], 4)
            obj["grade_scores"]     = grade_result["all_scores"]
            obj["action"]           = grade_result["action"]
        else:
            obj["grade"]   = None
            obj["action"]  = "Flag for human review"

        if vol_result:
            obj["volume_cm3"] = vol_result["volume_cm3"]
            obj["dimensions"] = {
                "width_cm":  vol_result["width_cm"],
                "height_cm": vol_result["height_cm"],
            }

        objects_out.append(obj)

    # ── Summary ───────────────────────────────────────────────────────────
    type_counts: Dict[str, int] = {}
    grade_counts: Dict[str, int] = {}
    total_volume = 0.0
    has_volume = False

    for obj in objects_out:
        t = obj["plastic_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
        g = obj.get("grade") or "Unknown"
        grade_counts[g] = grade_counts.get(g, 0) + 1
        v = obj.get("volume_cm3")
        if v is not None:
            total_volume += v
            has_volume = True

    # ── Annotated image ───────────────────────────────────────────────────
    annotated = _draw_detections(image, objects_out)
    buf = io.BytesIO()
    annotated.save(buf, format="JPEG", quality=88)
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # ── Build typed response ──────────────────────────────────────────────
    detected_objects = []
    for obj in objects_out:
        grade_scores_model = None
        if obj.get("grade_scores"):
            grade_scores_model = GradeScores(**obj["grade_scores"])

        dims_model = None
        if obj.get("dimensions"):
            dims_model = Dimensions(**obj["dimensions"])

        detected_objects.append(DetectedObject(
            object_id=obj["object_id"],
            bbox=obj["bbox"],
            detection_confidence=obj["detection_confidence"],
            plastic_type=obj["plastic_type"],
            type_confidence=obj["type_confidence"],
            all_class_scores=obj.get("all_class_scores"),
            grade=obj.get("grade"),
            grade_confidence=obj.get("grade_confidence"),
            grade_scores=grade_scores_model,
            action=obj.get("action"),
            volume_cm3=obj.get("volume_cm3"),
            dimensions=dims_model,
        ))

    summary = DetectionSummary(
        total_objects=len(objects_out),
        type_counts=type_counts,
        grade_counts=grade_counts,
        total_volume_cm3=round(total_volume, 1) if has_volume else None,
    )

    return DetectionResult(
        objects=detected_objects,
        summary=summary,
        annotated_image_b64=img_b64,
        detection_method=method,
    )
