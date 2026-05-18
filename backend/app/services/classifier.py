"""
RoBERTa-based fake news classifier.

Uses HuggingFace Transformers to load a fine-tuned RoBERTa model.
Default model: hamzab/roberta-fake-news-classification

To swap models, either:
  1. Change MODEL_NAME in config/env
  2. Subclass BaseClassifier with your own implementation
"""

import asyncio
import logging
from typing import Optional

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from app.services.base import (
    BaseClassifier,
    ClassificationResult,
    VerdictLabel,
)

logger = logging.getLogger(__name__)

# ── Label Mapping ─────────────────────────────────────────────
# Maps model output labels to our internal verdict system.
# Adjust this dict when swapping to a different model.
DEFAULT_LABEL_MAP = {
    # Add these new labels for the DeBERTa model
    "entailment": VerdictLabel.REAL,
    "contradiction": VerdictLabel.FAKE,
    "neutral": VerdictLabel.UNKNOWN,
    
    # Keep the old ones just in case
    "Fake":  VerdictLabel.FAKE,
    "Real":  VerdictLabel.REAL,
}



class RoBERTaClassifier(BaseClassifier):
    """
    HuggingFace RoBERTa classifier for fake news detection.

    Usage:
        classifier = RoBERTaClassifier()
        await classifier.load_model()
        result = await classifier.classify("Some news headline")
        print(result.label, result.confidence)
    """

    def __init__(
        self,
        model_name: str = "hamzab/roberta-fake-news-classification",
        label_map: Optional[dict] = None,
        device: Optional[str] = None,
        max_length: int = 512,
    ):
        self.model_name = model_name
        self.label_map = label_map or DEFAULT_LABEL_MAP
        self.max_length = max_length
        self._model = None
        self._tokenizer = None

        # Auto-detect device
        if device:
            self._device = torch.device(device)
        elif torch.cuda.is_available():
            self._device = torch.device("cuda")
        else:
            self._device = torch.device("cpu")

    # ── Interface Implementation ──────────────────────────────

    async def load_model(self) -> None:
        """Download and load model weights (runs in thread to avoid blocking)."""
        logger.info(f"Loading model: {self.model_name} on {self._device}")
        await asyncio.to_thread(self._load_sync)
        logger.info(f"Model loaded successfully: {self.model_name}")

    def _load_sync(self) -> None:
        """Synchronous model loading — called via asyncio.to_thread."""
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name
        ).to(self._device)
        self._model.eval()

    def is_loaded(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    async def classify(self, text: str) -> ClassificationResult:
        """
        Classify text as real or fake news.

        Returns a ClassificationResult with the predicted label,
        confidence score, and raw probability distribution.
        """
        if not self.is_loaded():
            raise RuntimeError(
                "Model not loaded. Call `await classifier.load_model()` first."
            )

        # Run inference in a thread to keep the event loop responsive
        return await asyncio.to_thread(self._classify_sync, text)

    def _classify_sync(self, text: str) -> ClassificationResult:
        """Synchronous inference — called via asyncio.to_thread."""
        # Tokenize
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding=True,
        ).to(self._device)

        # Inference (no gradient computation needed)
        with torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)[0]

        # Get prediction
        predicted_idx = torch.argmax(probabilities).item()
        confidence = probabilities[predicted_idx].item()

        # Map model label to our verdict
        id2label = self._model.config.id2label
        raw_label = id2label.get(predicted_idx, f"LABEL_{predicted_idx}")
        verdict_label = self.label_map.get(raw_label, VerdictLabel.UNKNOWN)

        # Build raw scores dict
        raw_scores = {}
        for idx, prob in enumerate(probabilities):
            label_name = id2label.get(idx, f"LABEL_{idx}")
            raw_scores[label_name] = round(prob.item(), 4)

        return ClassificationResult(
            label=verdict_label,
            confidence=round(confidence, 4),
            raw_scores=raw_scores,
        )
