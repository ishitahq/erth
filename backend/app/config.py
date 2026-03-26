"""
Central configuration — all constants extracted from pipeline-local.ipynb
and pipeline-inference.ipynb.
"""

from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# EfficientNet-B3 checkpoint (PyTorch — phase3_best.pth)
EFFICIENTNET_CHECKPOINT = MODELS_DIR / "phase3_best.pth"

# EfficientNet ONNX export (for faster CPU inference)
ONNX_CHECKPOINT = MODELS_DIR / "plastic_classifier.onnx"

# CLIP ViT-B/32 weights — download once, load from local path
# Download from: https://openaipublic.azureedge.net/clip/models/
#   40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt
# Place at: backend/models/ViT-B-32.pt  (~338 MB)
CLIP_CHECKPOINT = MODELS_DIR / "ViT-B-32.pt"
CLIP_DOWNLOAD_URL = (
    "https://openaipublic.azureedge.net/clip/models/"
    "40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt"
)

# Depth Anything V2 checkpoint — lives in backend/checkpoints/ (not models/)
DEPTH_CHECKPOINT = BASE_DIR / "checkpoints" / "depth_anything_v2_metric_indoor_vitl.pth"

# Path to the cloned Depth-Anything-V2 repo (metric_depth sub-dir)
DEPTH_REPO_PATH = BASE_DIR / "Depth-Anything-V2" / "metric_depth"

# ── Classification Constants ─────────────────────────────────────────────────
# ImageFolder sorts class names alphabetically — indices 0-5
CLASS_NAMES = ["HDPE", "LDPE", "OTHER", "PET", "PP", "PS"]
NUM_CLASSES = 6
IMG_SIZE = 300

# Confidence below this threshold → "Unknown — Flag for Review"
CONFIDENCE_THRESHOLD = 0.70

# ── ImageNet Normalization (used by EfficientNet) ────────────────────────────
IMG_MEAN = [0.485, 0.456, 0.406]
IMG_STD  = [0.229, 0.224, 0.225]

# ── CLIP Grade Descriptions (Step 8 from pipeline) ──────────────────────────
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
CAMERA_FOV_DEGREES = 60        # Standard industrial camera assumption
PLASTIC_THICKNESS_CM = 2.0    # Average plastic item thickness for volume proxy

# Foreground detection: pixels in the closest N% of depth values = the plastic item.
# Background pixels are excluded from width/height/depth calculations.
DEPTH_FG_PERCENTILE = 30      # lower 30% of depth = foreground object

# ── Depth Anything V2 Model Config ───────────────────────────────────────────
DEPTH_MODEL_CONFIGS = {
    "vits": {"encoder": "vits", "features": 64,  "out_channels": [48,  96,  192, 384]},
    "vitb": {"encoder": "vitb", "features": 128, "out_channels": [96,  192, 384, 768]},
    "vitl": {"encoder": "vitl", "features": 256, "out_channels": [256, 512, 1024, 1024]},
}
DEPTH_ENCODER = "vitl"
DEPTH_MAX_DEPTH = 20  # meters — indoor setting
