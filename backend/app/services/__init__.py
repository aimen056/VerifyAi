"""
Services module — ML pipeline, OCR, fact-checking, explainability.

Import convenience: everything is accessible from `app.services`.
"""

from app.services.base import (
    BaseClassifier,
    BaseProcessor,
    BaseFactChecker,
    ClassificationResult,
    OCRResult,
    FactCheckResult,
    FactCheckClaim,
    VerdictLabel,
)
from app.services.classifier import RoBERTaClassifier
from app.services.processor import TesseractProcessor
from app.services.fact_checker import GoogleFactChecker
from app.services.explainer import ShapExplainer
from app.services.pipeline import VerificationPipeline

__all__ = [
    # Abstract interfaces
    "BaseClassifier",
    "BaseProcessor",
    "BaseFactChecker",
    # Data classes
    "ClassificationResult",
    "OCRResult",
    "FactCheckResult",
    "FactCheckClaim",
    "VerdictLabel",
    # Concrete implementations
    "RoBERTaClassifier",
    "TesseractProcessor",
    "GoogleFactChecker",
    "ShapExplainer",
    "VerificationPipeline",
]
