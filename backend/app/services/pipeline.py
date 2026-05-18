"""
Verification Pipeline — orchestrator that connects all services.

This is the single entry-point the router calls. It coordinates:
  1. OCR text extraction (for image inputs)
  2. RoBERTa classification (verdict + confidence)
  3. SHAP explainability (transparent reasoning)
  4. Google Fact Check API (external evidence)

Designed for easy model/service swapping — just inject a different
implementation of BaseClassifier, BaseProcessor, or BaseFactChecker.
"""

import uuid
import time
import logging
from typing import Optional, List

from app.models.schemas import (
    VerifyResponse,
    VerdictEnum,
    SourceReference,
    ExplanationData,
    TokenAttribution,
    ModelScores,
)
from app.services.base import (
    ClassificationResult,
    VerdictLabel,
    OCRResult,
    FactCheckResult,
)
from app.services.classifier import RoBERTaClassifier
from app.services.processor import TesseractProcessor
from app.services.fact_checker import GoogleFactChecker
from app.services.explainer import ShapExplainer

logger = logging.getLogger(__name__)


# ── Label → API Verdict mapping ──────────────────────────────
_LABEL_TO_VERDICT = {
    VerdictLabel.REAL:       VerdictEnum.TRUE,
    VerdictLabel.FAKE:       VerdictEnum.FALSE,
    VerdictLabel.MISLEADING: VerdictEnum.MISLEADING,
    VerdictLabel.UNKNOWN:    VerdictEnum.UNVERIFIED,
}


from app.services.search_verifier import SearchVerifier

class VerificationPipeline:
    def __init__(
        self,
        classifier: RoBERTaClassifier,
        processor: TesseractProcessor,
        fact_checker: GoogleFactChecker,
        explainer: Optional[ShapExplainer] = None,
        search_verifier: Optional[SearchVerifier] = None,
    ):
        self.classifier = classifier
        self.processor = processor
        self.fact_checker = fact_checker
        self.explainer = explainer or ShapExplainer()
        self.search_verifier = search_verifier
        self._ready = False

    # ── Lifecycle ─────────────────────────────────────────────

    async def initialise(self) -> None:
        """Load model weights and initialise SHAP explainer."""
        await self.classifier.load_model()

        # Wire up SHAP with the loaded model internals
        if self.classifier.is_loaded():
            self.explainer.initialise(
                tokenizer=self.classifier._tokenizer,
                model=self.classifier._model,
                device=self.classifier._device,
            )
        self._ready = True
        logger.info("Verification pipeline initialised and ready.")

    @property
    def is_ready(self) -> bool:
        return self._ready and self.classifier.is_loaded()

    # ── Public Verification Methods ──────────────────────────

    async def verify_text(self, text: str) -> VerifyResponse:
        """
        Full verification pipeline for a text claim.

        Steps: classify → explain → fact-check → build response
        """
        start = time.perf_counter()

        # 0. Basic Validation for gibberish / single words
        if len(text.split()) < 4:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return VerifyResponse(
                id=str(uuid.uuid4()),
                verdict=VerdictEnum.UNVERIFIED,
                confidence=0.0,
                summary="The claim is too short to contain verifiable facts. Please provide a complete news headline or sentence.",
                sources=[],
                processing_time_ms=elapsed_ms,
            )

        # 1. Classify
        classification = await self.classifier.classify(text)

        # 2. SHAP explanation (best-effort, with timeout)
        explanation_text = ""
        explanation_tokens: list = []
        try:
            explanation_text, explanation_tokens = await self.explainer.explain(text)
        except Exception as e:
            logger.warning(f"SHAP explanation skipped: {e}")
            explanation_text = "Explanation unavailable."

        # 3. External fact-check (database)
        fact_result = await self.fact_checker.check(text)

        # 4. Real-time Web Search Verification
        search_results = []
        corroboration_score = 0.5
        corroboration_reason = ""
        if self.search_verifier:
            search_results = await self.search_verifier.search(text)
            corroboration_score, corroboration_reason = await self.search_verifier.verify_corroboration(text, search_results)

        # 5. Build unified response
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        return self._build_response(
            classification=classification,
            explanation=explanation_text,
            explanation_tokens=explanation_tokens,
            fact_result=fact_result,
            search_results=search_results,
            corroboration_score=corroboration_score,
            corroboration_reason=corroboration_reason,
            input_summary=text,
            elapsed_ms=elapsed_ms,
        )

    async def verify_image(
        self,
        image_bytes: bytes,
        description: Optional[str] = None,
    ) -> VerifyResponse:
        """
        Full verification pipeline for a screenshot.

        Steps: OCR → classify → explain → fact-check → build response
        """
        start = time.perf_counter()

        # 1. Extract text via OCR
        ocr_result = await self.processor.extract_text(image_bytes)

        if not ocr_result.text.strip():
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return VerifyResponse(
                id=str(uuid.uuid4()),
                verdict=VerdictEnum.UNVERIFIED,
                confidence=0.0,
                summary=(
                    "Could not extract any readable text from the image. "
                    "Please upload a clearer screenshot or paste the text directly."
                ),
                sources=[],
                processing_time_ms=elapsed_ms,
            )

        # Use OCR text (optionally enriched with user description)
        claim_text = ocr_result.text
        if description:
            claim_text = f"{description}\n\n{ocr_result.text}"

        # 2. Classify extracted text
        classification = await self.classifier.classify(claim_text)

        # 3. SHAP explanation
        explanation_text = ""
        explanation_tokens: list = []
        try:
            explanation_text, explanation_tokens = await self.explainer.explain(
                claim_text
            )
        except Exception as e:
            logger.warning(f"SHAP explanation skipped: {e}")
            explanation_text = "Explanation unavailable."

        # 4. Fact-check on extracted text
        fact_result = await self.fact_checker.check(ocr_result.text)

        # 5. Real-time Search on extracted text
        search_results = []
        corroboration_score = 0.5
        corroboration_reason = ""
        if self.search_verifier:
            search_results = await self.search_verifier.search(ocr_result.text)
            corroboration_score, corroboration_reason = await self.search_verifier.verify_corroboration(ocr_result.text, search_results)

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        response = self._build_response(
            classification=classification,
            explanation=explanation_text,
            explanation_tokens=explanation_tokens,
            fact_result=fact_result,
            search_results=search_results,
            corroboration_score=corroboration_score,
            corroboration_reason=corroboration_reason,
            input_summary=ocr_result.text,
            elapsed_ms=elapsed_ms,
        )

        # Prepend OCR metadata to the summary
        response.summary = (
            f"[OCR confidence: {ocr_result.confidence:.0%}] "
            + response.summary
        )

        return response

    async def verify_url(self, url: str, scraped_text: str = "") -> VerifyResponse:
        """
        Verify a news article URL.

        For now, delegates to verify_text with the URL string.
        A future upgrade can add web scraping here.
        """
        text = scraped_text if scraped_text else str(url)
        return await self.verify_text(text)

    # ── Internal Helpers ─────────────────────────────────────

    def _build_response(
        self,
        classification: ClassificationResult,
        explanation: str,
        explanation_tokens: list,
        fact_result: FactCheckResult,
        search_results: list,
        corroboration_score: float,
        corroboration_reason: str,
        input_summary: str,
        elapsed_ms: int,
    ) -> VerifyResponse:
        """
        Assemble the final response with user-friendly, non-technical summaries.
        """
        # 1. Base verdict from AI Stylistic Analysis
        base_verdict = _LABEL_TO_VERDICT.get(
            classification.label, VerdictEnum.UNVERIFIED
        )
        final_verdict = base_verdict
        confidence = classification.confidence
        override_reason = ""

        # 1.5. Factual Supremacy Logic (Override AI Verdict)
        if corroboration_score > 0.9:
            final_verdict = VerdictEnum.TRUE
            confidence = corroboration_score
        elif corroboration_score < 0.2:
            final_verdict = VerdictEnum.FALSE
            confidence = 0.95
        elif corroboration_score > 0.7:
            final_verdict = VerdictEnum.TRUE
            confidence = corroboration_score
        elif corroboration_score < 0.4:
            final_verdict = VerdictEnum.FALSE
            confidence = 0.8
        else:
            # Only fall back to AI style if search is truly ambiguous
            final_verdict = base_verdict
            confidence = classification.confidence

        # 2. Fact-Check Sources
        fact_sources = []
        for r in search_results:
            fact_sources.append(SourceReference(name=r.title, url=r.url))

        # 3. Generate Human-Friendly Summary
        style_desc = "neutral and journalistic" if classification.label == "REAL" else "sensational or opinionated"
        
        lead = ""
        if final_verdict == VerdictEnum.TRUE:
            lead = "✅ VERIFIED TRUE." if confidence > 0.9 else "✅ LIKELY TRUE."
        elif final_verdict == VerdictEnum.FALSE:
            lead = "❌ DISPROVEN." if confidence > 0.9 else "❌ LIKELY FALSE."
        else:
            lead = "⚠️ UNVERIFIED."

        # The reason now contains rich context
        summary = f"{lead} {corroboration_reason} The writing style appears {style_desc}."

        # 4. Build structured data
        explanation_data = ExplanationData(
            summary=explanation if explanation and "unavailable" not in explanation.lower() else "The AI used its internal knowledge to assess the style and facts.",
            tokens=[
                TokenAttribution(token=t["token"], attribution=t["attribution"])
                for t in explanation_tokens
            ],
        )

        return VerifyResponse(
            id=str(uuid.uuid4()),
            verdict=final_verdict,
            confidence=confidence,
            summary=summary,
            explanation=explanation_data,
            model_scores=ModelScores(scores=classification.raw_scores),
            sources=fact_sources,
            processing_time_ms=elapsed_ms,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.gmtime()),
        )
