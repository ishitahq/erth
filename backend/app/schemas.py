"""
Pydantic response schemas for the classification API.
"""

from pydantic import BaseModel


class GradeScores(BaseModel):
    """Per-grade confidence breakdown from CLIP zero-shot."""
    A: float | None = None
    B: float | None = None
    C: float | None = None


class Dimensions(BaseModel):
    """Estimated real-world dimensions in centimeters."""
    width_cm: float
    height_cm: float


class ClassificationResult(BaseModel):
    """Full hierarchical classification result for a single image."""

    # Stage 1 — EfficientNet-B3 type classification
    plastic_type: str  # one of CLASS_NAMES or "Unknown"
    type_confidence: float  # max softmax probability

    # Stage 2 — CLIP grade classification (nullable if CLIP unavailable)
    grade: str | None = None  # A, B, C, or None
    grade_confidence: float | None = None
    grade_scores: GradeScores | None = None
    action: str | None = None  # recommended recycling action

    # Stage 3 — Volumetric estimation (nullable if depth model unavailable)
    volume_cm3: float | None = None
    dimensions: Dimensions | None = None


class ModelStatus(BaseModel):
    """Availability status for each model."""
    efficientnet: bool = False
    clip: bool = False
    depth: bool = False


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    device: str = "cpu"
    models: ModelStatus = ModelStatus()
