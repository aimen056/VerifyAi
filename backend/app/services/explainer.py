"""
SHAP-based explainability for the RoBERTa classifier.

Generates human-readable explanations of *why* a claim was
classified as REAL / FAKE / MISLEADING, using SHAP token
attributions.

Runs the heavy computation in a thread with a timeout to keep
the API responsive. Falls back to a simple confidence-based
explanation if SHAP takes too long.
"""

import asyncio
import logging
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import torch

logger = logging.getLogger(__name__)

# Guard import — shap is optional at import time; we fail
# gracefully if it's missing so the rest of the pipeline can
# still function without explanations.
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP not installed — explanations will be unavailable.")

# Dedicated thread pool for SHAP (prevents blocking other inference)
_shap_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="shap")


class ShapExplainer:
    """
    SHAP explainer wrapper for HuggingFace text classification models.

    Usage:
        explainer = ShapExplainer()
        explainer.initialise(tokenizer, model, device)
        summary, tokens = await explainer.explain("Some claim text")
    """

    def __init__(
        self,
        max_tokens_display: int = 10,
        timeout_seconds: float = 30.0,
    ):
        """
        Args:
            max_tokens_display: Number of top attribution tokens
                                to include in the explanation.
            timeout_seconds:    Max time for SHAP computation before
                                falling back to a simple explanation.
        """
        self.max_tokens_display = max_tokens_display
        self.timeout_seconds = timeout_seconds
        self._explainer: Optional[object] = None
        self._tokenizer = None
        self._model = None
        self._device = None

    # ── Setup ─────────────────────────────────────────────────

    def initialise(self, tokenizer, model, device) -> None:
        """
        Create the SHAP explainer once the model is loaded.

        Must be called AFTER the classifier's load_model().
        """
        if not SHAP_AVAILABLE:
            logger.warning("SHAP not available — skipping initialisation.")
            return

        self._tokenizer = tokenizer
        self._model = model
        self._device = device

        # Build a pipeline function that SHAP can call
        def _predict(texts) -> np.ndarray:
            # SHAP passes numpy arrays; tokenizer requires a list of strings
            texts_list = texts.tolist() if hasattr(texts, "tolist") else list(texts)
            inputs = self._tokenizer(
                texts_list,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512,
            ).to(self._device)
            with torch.no_grad():
                logits = self._model(**inputs).logits
            return torch.softmax(logits, dim=-1).cpu().numpy()

        self._explainer = shap.Explainer(
            _predict,
            self._tokenizer,
            output_names=list(self._model.config.id2label.values()),
        )
        logger.info("SHAP explainer initialised successfully.")

    @property
    def is_ready(self) -> bool:
        return self._explainer is not None

    # ── Public API ────────────────────────────────────────────

    async def explain(self, text: str) -> Tuple[str, List[dict]]:
        """
        Generate a SHAP-based explanation for a classification.

        Has a timeout — if SHAP takes longer than timeout_seconds,
        returns a fallback explanation instead of blocking.

        Returns:
            summary:  A human-readable paragraph explaining the verdict.
            tokens:   List of dicts with "token" and "attribution" keys,
                      sorted by absolute attribution (descending).
        """
        if not self.is_ready:
            return (
                "Explanation unavailable — SHAP explainer not initialised.",
                [],
            )

        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(_shap_executor, self._explain_sync, text),
                timeout=self.timeout_seconds,
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(
                f"SHAP explanation timed out after {self.timeout_seconds}s — "
                "using fallback explanation."
            )
            return (
                "Detailed token-level explanation timed out. "
                "The verdict is based on the model's full analysis of the text.",
                [],
            )
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}", exc_info=True)
            return (
                "Explanation could not be generated due to an internal error.",
                [],
            )

    def _explain_sync(self, text: str) -> Tuple[str, List[dict]]:
        """Synchronous SHAP computation — runs in a dedicated thread."""
        try:
            # Truncate very long text for SHAP (it scales quadratically)
            truncated = text[:300] if len(text) > 300 else text

            shap_values = self._explainer([truncated])
            sample_exp = shap_values[0]

            # Get values for the first (and only) sample
            base_vals = sample_exp.base_values    # (n_classes,)
            token_vals = sample_exp.values         # (n_tokens, n_classes)
            tokens_data = sample_exp.data          # (n_tokens,)

            # Sum SHAP values + base to find predicted class
            total = base_vals + token_vals.sum(axis=0)
            pred_class = int(np.argmax(total))

            # Attribution for the predicted class per token
            attributions = token_vals[:, pred_class]

            # Build token list sorted by absolute attribution
            token_list = []
            for tok, attr in zip(tokens_data, attributions):
                tok_str = str(tok).strip()
                if not tok_str or tok_str in ("[CLS]", "[SEP]", "<s>", "</s>"):
                    continue
                token_list.append({
                    "token": tok_str,
                    "attribution": round(float(attr), 4),
                })

            token_list.sort(key=lambda x: abs(x["attribution"]), reverse=True)
            top_tokens = token_list[: self.max_tokens_display]

            # Build human-readable summary
            supporting = [t for t in top_tokens if t["attribution"] > 0]
            opposing = [t for t in top_tokens if t["attribution"] < 0]

            parts = []
            if supporting:
                words = ", ".join(f'"{t["token"]}"' for t in supporting[:5])
                parts.append(
                    f"Key words pushing toward this verdict: {words}."
                )
            if opposing:
                words = ", ".join(f'"{t["token"]}"' for t in opposing[:5])
                parts.append(
                    f"Words pushing against this verdict: {words}."
                )

            summary = " ".join(parts) if parts else (
                "The model did not strongly rely on any individual words."
            )

            return summary, top_tokens

        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}", exc_info=True)
            return (
                "Explanation could not be generated due to an internal error.",
                [],
            )
