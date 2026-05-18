"""
Abstract base classes for all AI services.
Swap any implementation by subclassing these interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


# ── Shared Data Classes ───────────────────────────────────────

class VerdictLabel(str, Enum):
    """Internal verdict labels used by classifiers."""
    REAL = "REAL"
    FAKE = "FAKE"
    MISLEADING = "MISLEADING"
    UNKNOWN = "UNKNOWN"


@dataclass
class ClassificationResult:
    """Output from any text classifier."""
    label: VerdictLabel
    confidence: float           # 0.0 – 1.0
    raw_scores: dict = field(default_factory=dict)  # all class probabilities


@dataclass
class OCRResult:
    """Output from any OCR processor."""
    text: str
    language: str = "en"
    confidence: float = 0.0     # average character confidence


@dataclass
class FactCheckClaim:
    """A single claim returned by a fact-checking source."""
    claim_text: str
    claimant: Optional[str] = None
    rating: Optional[str] = None        # e.g. "False", "Mostly True"
    source_name: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class FactCheckResult:
    """Aggregated output from fact-check lookups."""
    claims: List[FactCheckClaim] = field(default_factory=list)
    query: str = ""


# ── Abstract Interfaces ──────────────────────────────────────

class BaseClassifier(ABC):
    """Interface for text classification models."""

    @abstractmethod
    async def load_model(self) -> None:
        """Pre-load model weights into memory."""
        ...

    @abstractmethod
    async def classify(self, text: str) -> ClassificationResult:
        """Classify a piece of text and return a verdict."""
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if the model is ready for inference."""
        ...


class BaseProcessor(ABC):
    """Interface for image/document processors (OCR, forensics, etc.)."""

    @abstractmethod
    async def extract_text(self, image_bytes: bytes) -> OCRResult:
        """Extract text from an image."""
        ...


class BaseFactChecker(ABC):
    """Interface for external fact-checking services."""

    @abstractmethod
    async def check(self, claim: str) -> FactCheckResult:
        """Look up a claim against external fact-check databases."""
        ...
