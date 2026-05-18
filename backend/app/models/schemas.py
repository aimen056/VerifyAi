"""
Pydantic schemas for verification requests and responses.
Aligned with the PRD verdict system: TRUE | FALSE | MISLEADING | UNVERIFIED
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


# ── Verdict Enum ──────────────────────────────────────────────
class VerdictEnum(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    MISLEADING = "MISLEADING"
    UNVERIFIED = "UNVERIFIED"


# ── Request Models ────────────────────────────────────────────
class TextVerifyRequest(BaseModel):
    """UC-01: User pastes a headline or article text for verification."""
    text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="The news headline or article text to verify.",
        examples=["Breaking: Scientists discover water on Mars"],
    )


class ImageVerifyRequest(BaseModel):
    """UC-02: User uploads a screenshot for OCR + forensics analysis.
    The actual file is sent as multipart form data; this model
    captures optional metadata sent alongside the upload."""
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional context about the screenshot.",
    )


class URLVerifyRequest(BaseModel):
    """UC-03: System scrapes a news URL to assess credibility."""
    url: HttpUrl = Field(
        ...,
        description="The news article URL to scrape and verify.",
        examples=["https://example.com/breaking-news-article"],
    )


# ── Response Models ───────────────────────────────────────────
class SourceReference(BaseModel):
    """A single fact-check or credibility source."""
    name: str
    url: Optional[str] = None
    trust_score: Optional[float] = Field(None, ge=0, le=1)


class TokenAttribution(BaseModel):
    """A single token's SHAP attribution score."""
    token: str
    attribution: float = Field(..., description="Positive = supports verdict, negative = opposes.")


class ExplanationData(BaseModel):
    """Structured SHAP explanation data for transparent verdicts."""
    summary: str = Field("", description="Human-readable explanation of model reasoning.")
    tokens: List[TokenAttribution] = Field(
        default_factory=list,
        description="Top tokens by attribution magnitude.",
    )


class ModelScores(BaseModel):
    """Raw model output probabilities for each label."""
    scores: dict = Field(default_factory=dict, description="Label → probability mapping.")


class VerifyResponse(BaseModel):
    """Unified response returned by all /verify/* endpoints."""
    model_config = {'protected_namespaces': ()}
    
    id: str = Field(..., description="Unique verification request ID.")
    verdict: VerdictEnum
    confidence: float = Field(..., ge=0, le=1, description="Model confidence 0-1.")
    summary: str = Field(..., description="Human-readable explanation of the verdict.")
    explanation: ExplanationData = Field(
        default_factory=ExplanationData,
        description="SHAP-based explainability data.",
    )
    model_scores: ModelScores = Field(
        default_factory=ModelScores,
        description="Raw model label probabilities.",
    )
    sources: List[SourceReference] = Field(
        default_factory=list,
        description="Supporting sources used in the verdict.",
    )
    processing_time_ms: int = Field(..., description="Wall-clock processing time.")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health-check response."""
    status: str = "ok"
    version: str
    services: dict = Field(
        default_factory=dict,
        description="Status of downstream services (db, redis, etc.).",
    )
