"""
FastAPI application — Plastic Waste Classification API.

Endpoints:
  GET  /health    → model availability + device info
  POST /classify  → single-item: upload image, returns hierarchical classification
  POST /detect    → conveyor belt: detect all plastic items, classify each one
"""

import logging
from io import BytesIO

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from .inference import detect_and_classify, run_full_pipeline
from .models import DEVICE, load_clip, load_depth_model, load_efficientnet, load_onnx_session
from .schemas import ClassificationResult, DetectionResult, HealthResponse, ModelStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Plastic Waste Classification API",
    description=(
        "Hierarchical plastic waste classification pipeline:\\n"
        "- **Stage 1** — EfficientNet-B3 (PyTorch or ONNX): plastic type\\n"
        "- **Stage 2** — CLIP ViT-B/32 zero-shot: recyclability grade (A/B/C)\\n"
        "- **Stage 3** — Depth Anything V2: volumetric estimation (cm³)\\n"
        "- **/detect** — conveyor belt mode: detects multiple objects, classifies each"
    ),
    version="1.2.0",
)

# ── CORS (for React frontend on Vite / CRA dev server) ───────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite default
        "http://localhost:3000",   # CRA / Next.js
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*",                       # open during hackathon — restrict in prod
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Check which models are loaded and report device info."""
    return HealthResponse(
        status="ok",
        device=str(DEVICE),
        models=ModelStatus(
            efficientnet_pytorch=load_efficientnet() is not None,
            efficientnet_onnx=load_onnx_session() is not None,
            clip=load_clip() is not None,
            depth=load_depth_model() is not None,
        ),
    )


# ── Classify ─────────────────────────────────────────────────────────────────

@app.post("/classify", response_model=ClassificationResult)
async def classify_image(
    file: UploadFile = File(..., description="Image file (JPEG / PNG / WEBP) to classify"),
    use_tta: bool = Query(
        False,
        description=(
            "Enable Test-Time Augmentation (8 deterministic views averaged). "
            "Slower but more robust. Forces PyTorch backend."
        ),
    ),
    use_onnx: bool = Query(
        True,
        description=(
            "Prefer ONNX runtime for Stage 1 when available "
            "(faster on CPU, ignored when use_tta=true)."
        ),
    ),
):
    """
    Upload an image and receive a full hierarchical classification:

    - **plastic_type**: PET | HDPE | LDPE | PP | PS | OTHER | Unknown
    - **type_confidence**: max softmax probability (0–1)
    - **all_class_scores**: per-class probability breakdown
    - **grade**: A (recycle) | B (pre-process) | C (reject) — needs CLIP
    - **grade_confidence**: CLIP cosine-similarity score
    - **action**: recommended recycling action
    - **volume_cm3**: estimated volume proxy — needs Depth Anything V2
    - **backend_used**: pytorch | onnx
    """
    # Validate content type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Expected an image file, got {file.content_type!r}",
        )

    # Read + decode image
    try:
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode image: {exc}")

    # Run the full 3-stage pipeline
    try:
        result = run_full_pipeline(image, use_tta=use_tta, prefer_onnx=use_onnx)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return result


# ── Detect ───────────────────────────────────────────────────────────────────

@app.post("/detect", response_model=DetectionResult)
async def detect_image(
    file: UploadFile = File(..., description="Conveyor belt image (JPEG / PNG / WEBP)"),
    use_onnx: bool = Query(
        True,
        description="Prefer ONNX runtime for Stage 1 (faster on CPU).",
    ),
):
    """
    Detect and classify **all** plastic items in a conveyor belt image.

    Returns for each detected object:
    - **bbox**: [x1, y1, x2, y2] bounding box in pixels
    - **plastic_type**: PET | HDPE | LDPE | PP | PS | OTHER | Unknown
    - **type_confidence**: EfficientNet softmax max probability
    - **grade**: A / B / C recyclability grade (CLIP)
    - **action**: recommended recycling action
    - **volume_cm3**: per-object volume estimate

    Also returns:
    - **summary**: total counts per type and grade, total volume
    - **annotated_image_b64**: base64 JPEG with colour-coded bounding boxes
    - **detection_method**: 'yolo' | 'opencv' | 'full_image_fallback'
    """
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Expected an image file, got {file.content_type!r}",
        )

    try:
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode image: {exc}")

    try:
        result = detect_and_classify(image, prefer_onnx=use_onnx)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return result
