"""
FastAPI application — Plastic Waste Classification API.

Endpoints:
  GET  /health    → model availability and device info
  POST /classify  → upload image, get full classification result
"""

import logging
from io import BytesIO

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from .inference import run_full_pipeline
from .models import DEVICE, load_clip, load_depth_model, load_efficientnet
from .schemas import ClassificationResult, HealthResponse, ModelStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Plastic Waste Classification API",
    description=(
        "Hierarchical plastic waste classification pipeline: "
        "type (EfficientNet-B3) → grade (CLIP) → volumetric (Depth Anything V2)"
    ),
    version="1.0.0",
)

# ── CORS (for React frontend on Vite dev server) ────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # CRA / Next.js default
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Check which models are loaded and available."""
    return HealthResponse(
        status="ok",
        device=str(DEVICE),
        models=ModelStatus(
            efficientnet=load_efficientnet() is not None,
            clip=load_clip() is not None,
            depth=load_depth_model() is not None,
        ),
    )


# ── Classify ─────────────────────────────────────────────────────────────────

@app.post("/classify", response_model=ClassificationResult)
async def classify_image(
    file: UploadFile = File(..., description="Image file (JPEG/PNG) to classify"),
    use_tta: bool = Query(
        False,
        description=(
            "Enable Test-Time Augmentation (8 views). "
            "Slower but more robust for real-world images."
        ),
    ),
):
    """
    Upload an image and receive full hierarchical classification:

    - **Type**: PET, HDPE, LDPE, PP, PS, OTHER (or Unknown if low confidence)
    - **Grade**: A (recycle), B (pre-process), C (reject) — requires CLIP
    - **Volume**: Estimated volume in cm³ — requires Depth Anything V2
    """
    # Validate content type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Expected image file, got {file.content_type}",
        )

    # Read and open image
    try:
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read image: {exc}",
        )

    # Run pipeline
    try:
        result = run_full_pipeline(image, use_tta=use_tta)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return result
