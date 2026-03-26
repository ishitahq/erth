"""
Pydantic response schemas for the classification API.
"""

from typing import Optional
from pydantic import BaseModel


class GradeScores(BaseModel):
    """Per-grade confidence breakdown from CLIP zero-shot."""
    A: Optional[float] = None
    B: Optional[float] = None
    C: Optional[float] = None


class Dimensions(BaseModel):
    """Estimated real-world dimensions in centimeters."""
    width_cm: float
    height_cm: float


class ClassificationResult(BaseModel):
    """Full hierarchical classification result for a single image."""

    # Stage 1 — EfficientNet-B3 type classification
    plastic_type: str          # one of CLASS_NAMES or "Unknown"
    type_confidence: float     # max softmax probability
    all_class_scores: Optional[dict] = None  # per-class softmax probabilities

    # Stage 2 — CLIP grade classification (nullable if CLIP unavailable)
    grade: Optional[str] = None              # A, B, C, or None
    grade_confidence: Optional[float] = None
    grade_scores: Optional[GradeScores] = None
    action: Optional[str] = None             # recommended recycling action

    # Stage 3 — Volumetric estimation (nullable if depth model unavailable)
    volume_cm3: Optional[float] = None
    dimensions: Optional[Dimensions] = None

    # Meta
    backend_used: str = "pytorch"  # "pytorch" or "onnx"
    tta_used: bool = False


class ModelStatus(BaseModel):
    """Availability status for each model."""
    efficientnet_pytorch: bool = False
    efficientnet_onnx: bool = False
    clip: bool = False
    depth: bool = False


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    device: str = "cpu"
    models: ModelStatus = ModelStatus()
