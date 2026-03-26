"""
Central configuration — all constants extracted from pipeline-local.ipynb.
"""

from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
CHECKPOINT_DIR = BASE_DIR / "checkpoints"
CHECKPOINT_DIR.mkdir(exist_ok=True)

# EfficientNet-B3 checkpoint (phase3_best.pth from notebook Step 4)
EFFICIENTNET_CHECKPOINT = CHECKPOINT_DIR / "phase3_best.pth"

# Depth Anything V2 checkpoint (optional)
DEPTH_CHECKPOINT = CHECKPOINT_DIR / "depth_anything_v2_metric_indoor_vitl.pth"

# ── Classification Constants ─────────────────────────────────────────────────
# ImageFolder sorts class names alphabetically — indices 0-5
CLASS_NAMES = ["HDPE", "LDPE", "OTHER", "PET", "PP", "PS"]
NUM_CLASSES = 6
IMG_SIZE = 300

# Confidence below this threshold → "Unknown — Flag for Review"
CONFIDENCE_THRESHOLD = 0.70

# ── ImageNet Normalization (used by EfficientNet) ────────────────────────────
IMG_MEAN = [0.485, 0.456, 0.406]
IMG_STD = [0.229, 0.224, 0.225]

# ── CLIP Grade Descriptions (Step 8) ────────────────────────────────────────
GRADE_LABELS = ["A", "B", "C"]

GRADE_DESCRIPTIONS = [
    "a clean intact plastic item in good condition suitable for recycling",
    "a slightly dirty or mildly damaged plastic item that needs processing before recycling",
    "a heavily contaminated crushed or severely damaged plastic item not suitable for recycling",
]

GRADE_ACTIONS = {
    "A": "Send directly to recycling stream",
    "B": "Pre-process before recycling",
    "C": "Reject — do not recycle",
}

# ── Volumetric Estimation Constants (Step 9) ─────────────────────────────────
CAMERA_FOV_DEGREES = 60  # Standard industrial camera assumption
PLASTIC_THICKNESS_CM = 2.0  # Average plastic item thickness for volume proxy

# ── Depth Anything V2 Model Config ───────────────────────────────────────────
DEPTH_MODEL_CONFIGS = {
    "vits": {"encoder": "vits", "features": 64, "out_channels": [48, 96, 192, 384]},
    "vitb": {"encoder": "vitb", "features": 128, "out_channels": [96, 192, 384, 768]},
    "vitl": {"encoder": "vitl", "features": 256, "out_channels": [256, 512, 1024, 1024]},
}
DEPTH_ENCODER = "vitl"
DEPTH_MAX_DEPTH = 20  # meters — indoor setting
