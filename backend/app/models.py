"""
Model loading with lazy initialization — models cached globally.

Each loader returns None if the checkpoint / dependency is missing,
allowing the API to gracefully degrade.
"""

import logging
from typing import Any

import torch
import torch.nn as nn

from .config import (
    CLASS_NAMES,
    DEPTH_CHECKPOINT,
    DEPTH_ENCODER,
    DEPTH_MAX_DEPTH,
    DEPTH_MODEL_CONFIGS,
    EFFICIENTNET_CHECKPOINT,
    GRADE_DESCRIPTIONS,
    NUM_CLASSES,
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

_efficientnet: nn.Module | None = None
_clip_model: Any = None
_clip_preprocess: Any = None
_clip_text_features: torch.Tensor | None = None
_depth_model: Any = None


# ── EfficientNet-B3 ─────────────────────────────────────────────────────────

def _build_efficientnet() -> nn.Module:
    """Build EfficientNet-B3 with the custom 6-class classifier head from the notebook."""
    try:
        from torchvision.models import efficientnet_b3
        model = efficientnet_b3(weights=None)
    except ImportError:
        import torchvision
        model = torchvision.models.efficientnet_b3(pretrained=False)

    # Custom classifier head matching notebook Step 4
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(1536, 512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(512, NUM_CLASSES),
    )
    return model


def load_efficientnet() -> nn.Module | None:
    """Load EfficientNet-B3 from checkpoint. Returns None if checkpoint missing."""
    global _efficientnet
    if _efficientnet is not None:
        return _efficientnet

    if not EFFICIENTNET_CHECKPOINT.exists():
        logger.warning(
            "EfficientNet checkpoint not found at %s. "
            "Place phase3_best.pth in backend/checkpoints/",
            EFFICIENTNET_CHECKPOINT,
        )
        return None

    logger.info("Loading EfficientNet-B3 from %s ...", EFFICIENTNET_CHECKPOINT)
    model = _build_efficientnet()

    state_dict = torch.load(EFFICIENTNET_CHECKPOINT, map_location=DEVICE)
    # Handle both raw state_dict and wrapped format
    if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
        state_dict = state_dict["model_state_dict"]

    model.load_state_dict(state_dict)
    model.to(DEVICE).eval()
    _efficientnet = model
    logger.info("EfficientNet-B3 loaded on %s", DEVICE)
    return _efficientnet


# ── CLIP ViT-B/32 ───────────────────────────────────────────────────────────

def load_clip() -> tuple[Any, Any, torch.Tensor] | None:
    """
    Load CLIP ViT-B/32 and pre-encode grade text features.
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
            "Install with: pip install git+https://github.com/openai/CLIP.git"
        )
        return None

    logger.info("Loading CLIP ViT-B/32 ...")
    _clip_model, _clip_preprocess = clip.load("ViT-B/32", device=DEVICE)
    _clip_model.eval()

    # Pre-encode grade descriptions (done once, reused for all images)
    with torch.no_grad():
        text_tokens = clip.tokenize(GRADE_DESCRIPTIONS).to(DEVICE)
        _clip_text_features = _clip_model.encode_text(text_tokens)
        _clip_text_features = _clip_text_features / _clip_text_features.norm(
            dim=-1, keepdim=True
        )

    logger.info("CLIP loaded on %s", DEVICE)
    return _clip_model, _clip_preprocess, _clip_text_features


# ── Depth Anything V2 ───────────────────────────────────────────────────────

def load_depth_model() -> Any | None:
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

    try:
        from depth_anything_v2.dpt import DepthAnythingV2
    except ImportError:
        logger.warning(
            "depth_anything_v2 not installed. Volumetric estimation unavailable. "
            "See: https://github.com/DepthAnything/Depth-Anything-V2"
        )
        return None

    logger.info("Loading Depth Anything V2 (%s) ...", DEPTH_ENCODER)
    config = DEPTH_MODEL_CONFIGS[DEPTH_ENCODER]
    _depth_model = DepthAnythingV2(**config, max_depth=DEPTH_MAX_DEPTH)
    _depth_model.load_state_dict(
        torch.load(DEPTH_CHECKPOINT, map_location=DEVICE)
    )
    _depth_model.to(DEVICE).eval()
    logger.info("Depth model loaded on %s", DEVICE)
    return _depth_model
