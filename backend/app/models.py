"""
Model loading with lazy initialization — all models cached globally.

Load priority:
  - EfficientNet: PyTorch (.pth) first, ONNX (.onnx) as fallback for CPU
  - CLIP: openai/CLIP package (install separately)
  - Depth: Depth Anything V2 (optional, requires manual install)

All loaders return None if the checkpoint or dependency is missing,
allowing the API to gracefully degrade per stage.
"""

import logging
from typing import Any, Optional, Tuple

import torch
import torch.nn as nn

from .config import (
    CLASS_NAMES,
    CLIP_CHECKPOINT,
    CLIP_DOWNLOAD_URL,
    DEPTH_CHECKPOINT,
    DEPTH_ENCODER,
    DEPTH_MAX_DEPTH,
    DEPTH_MODEL_CONFIGS,
    DEPTH_REPO_PATH,
    EFFICIENTNET_CHECKPOINT,
    GRADE_DESCRIPTIONS,
    NUM_CLASSES,
    ONNX_CHECKPOINT,
)

logger = logging.getLogger(__name__)

# ── Device detection ─────────────────────────────────────────────────────────

def get_device() -> torch.device:
    """Auto-detect best available device: CUDA > MPS > CPU."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


DEVICE = get_device()

# ── Global model cache ───────────────────────────────────────────────────────

_efficientnet: Optional[nn.Module] = None
_onnx_session: Optional[Any] = None
_clip_model: Optional[Any] = None
_clip_preprocess: Optional[Any] = None
_clip_text_features: Optional[torch.Tensor] = None
_depth_model: Optional[Any] = None


# ── EfficientNet-B3 (PyTorch) ────────────────────────────────────────────────

def _build_efficientnet() -> nn.Module:
    """
    Build EfficientNet-B3 with the custom 6-class classifier head.
    Matches notebook Step 4: Dropout(0.3) → Linear(1536, 512) → ReLU → Dropout(0.2) → Linear(512, 6)
    """
    try:
        from torchvision.models import efficientnet_b3, EfficientNet_B3_Weights
        model = efficientnet_b3(weights=None)
    except (ImportError, TypeError):
        import torchvision
        model = torchvision.models.efficientnet_b3(pretrained=False)

    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(1536, 512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(512, NUM_CLASSES),
    )
    return model


def load_efficientnet() -> Optional[nn.Module]:
    """Load EfficientNet-B3 from .pth checkpoint. Returns None if missing."""
    global _efficientnet
    if _efficientnet is not None:
        return _efficientnet

    if not EFFICIENTNET_CHECKPOINT.exists():
        logger.warning(
            "EfficientNet checkpoint not found at %s. "
            "Place phase3_best.pth in backend/models/",
            EFFICIENTNET_CHECKPOINT,
        )
        return None

    logger.info("Loading EfficientNet-B3 (PyTorch) from %s ...", EFFICIENTNET_CHECKPOINT)
    model = _build_efficientnet()

    # Handles both raw state_dict and {'model_state_dict': ...} wrapped format
    checkpoint = torch.load(
        EFFICIENTNET_CHECKPOINT,
        map_location=DEVICE,
        weights_only=False,
    )
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.to(DEVICE).eval()
    _efficientnet = model
    logger.info("EfficientNet-B3 loaded on %s", DEVICE)
    return _efficientnet


# ── EfficientNet (ONNX) ──────────────────────────────────────────────────────

def load_onnx_session() -> Optional[Any]:
    """
    Load ONNX runtime inference session from plastic_classifier.onnx.
    Preferred backend for CPU inference. Returns None if unavailable.
    """
    global _onnx_session
    if _onnx_session is not None:
        return _onnx_session

    if not ONNX_CHECKPOINT.exists():
        logger.warning(
            "ONNX model not found at %s. Place plastic_classifier.onnx in backend/models/",
            ONNX_CHECKPOINT,
        )
        return None

    try:
        import onnxruntime as ort
    except ImportError:
        logger.warning("onnxruntime not installed. ONNX inference unavailable. pip install onnxruntime")
        return None

    logger.info("Loading ONNX session from %s ...", ONNX_CHECKPOINT)
    providers = (
        ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if torch.cuda.is_available()
        else ["CPUExecutionProvider"]
    )
    _onnx_session = ort.InferenceSession(str(ONNX_CHECKPOINT), providers=providers)
    logger.info("ONNX session ready (providers: %s)", _onnx_session.get_providers())
    return _onnx_session


# ── CLIP ViT-B/32 ───────────────────────────────────────────────────────────

def load_clip() -> Optional[Tuple[Any, Any, torch.Tensor]]:
    """
    Load CLIP ViT-B/32 and pre-encode grade text features.

    Load order:
      1. Local file  backend/models/ViT-B-32.pt  (preferred — no network needed)
      2. Auto-download via clip.load('ViT-B/32')  (fallback, ~338 MB)

    Returns (model, preprocess, text_features) or None if clip not installed.
    """
    global _clip_model, _clip_preprocess, _clip_text_features
    if _clip_model is not None:
        return _clip_model, _clip_preprocess, _clip_text_features

    try:
        import clip
    except ImportError:
        logger.warning(
            "CLIP not installed. Grade classification unavailable. "
            "Install: pip install git+https://github.com/openai/CLIP.git"
        )
        return None

    # Prefer local file so Docker/HF Spaces doesn't re-download on every cold start
    if CLIP_CHECKPOINT.exists():
        logger.info("Loading CLIP ViT-B/32 from local file %s ...", CLIP_CHECKPOINT)
        _clip_model, _clip_preprocess = clip.load(str(CLIP_CHECKPOINT), device=DEVICE)
    else:
        logger.warning(
            "CLIP local weights not found at %s. "
            "Falling back to auto-download (~338 MB). "
            "To avoid this, download: %s  "
            "and place it at backend/models/ViT-B-32.pt",
            CLIP_CHECKPOINT,
            CLIP_DOWNLOAD_URL,
        )
        _clip_model, _clip_preprocess = clip.load("ViT-B/32", device=DEVICE)

    _clip_model.eval()

    # Pre-encode grade descriptions once; reused for every image
    with torch.no_grad():
        text_tokens = clip.tokenize(GRADE_DESCRIPTIONS).to(DEVICE)
        _clip_text_features = _clip_model.encode_text(text_tokens)
        _clip_text_features = _clip_text_features / _clip_text_features.norm(
            dim=-1, keepdim=True
        )

    logger.info("CLIP loaded on %s", DEVICE)
    return _clip_model, _clip_preprocess, _clip_text_features


# ── Depth Anything V2 ───────────────────────────────────────────────────────

def load_depth_model() -> Optional[Any]:
    """Load Depth Anything V2 metric indoor model. Returns None if unavailable."""
    global _depth_model
    if _depth_model is not None:
        return _depth_model

    if not DEPTH_CHECKPOINT.exists():
        logger.warning(
            "Depth Anything V2 checkpoint not found at %s. "
            "Volumetric estimation unavailable.",
            DEPTH_CHECKPOINT,
        )
        return None

    # Ensure the cloned repo is on sys.path before importing
    import sys
    depth_repo_str = str(DEPTH_REPO_PATH)
    if depth_repo_str not in sys.path:
        sys.path.insert(0, depth_repo_str)

    try:
        from depth_anything_v2.dpt import DepthAnythingV2
    except ImportError:
        logger.warning(
            "depth_anything_v2 not installed. Volumetric estimation unavailable. "
            "Clone the repo: git clone https://github.com/DepthAnything/Depth-Anything-V2 "
            "into backend/ and run: pip install -r Depth-Anything-V2/metric_depth/requirements.txt"
        )
        return None

    logger.info("Loading Depth Anything V2 (%s) ...", DEPTH_ENCODER)
    config = DEPTH_MODEL_CONFIGS[DEPTH_ENCODER]
    _depth_model = DepthAnythingV2(**config, max_depth=DEPTH_MAX_DEPTH)
    _depth_model.load_state_dict(
        torch.load(DEPTH_CHECKPOINT, map_location=DEVICE, weights_only=False)
    )
    _depth_model.to(DEVICE).eval()
    logger.info("Depth model loaded on %s", DEVICE)
    return _depth_model
