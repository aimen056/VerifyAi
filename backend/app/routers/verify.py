"""
/verify endpoints — wired to the real ML verification pipeline.

Phase 2: RoBERTa classification, SHAP explainability,
Google Fact Check API, and Tesseract OCR.
"""

import time
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from app.models import (
    TextVerifyRequest,
    ImageVerifyRequest,
    URLVerifyRequest,
    VerifyResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verify", tags=["Verification"])

# ── Pipeline reference (set by main.py on startup) ───────────
# This is populated by the lifespan handler so the router
# doesn't own the lifecycle of the heavy ML objects.
_pipeline = None


def set_pipeline(pipeline) -> None:
    """Called by main.py after the pipeline is initialised."""
    global _pipeline
    _pipeline = pipeline


def _get_pipeline():
    """Retrieve the pipeline or raise 503 if not yet loaded."""
    if _pipeline is None or not _pipeline.is_ready:
        raise HTTPException(
            status_code=503,
            detail="ML pipeline is still loading. Please try again shortly.",
        )
    return _pipeline


# ── UC-01: Text Verification ─────────────────────────────────
@router.post(
    "/text",
    response_model=VerifyResponse,
    summary="Verify a text claim or headline",
)
async def verify_text(body: TextVerifyRequest):
    pipeline = _get_pipeline()
    return await pipeline.verify_text(body.text)


# ── UC-02: Screenshot / Image Verification ───────────────────
@router.post(
    "/image",
    response_model=VerifyResponse,
    summary="Verify an uploaded screenshot via OCR + classification",
)
async def verify_image(
    file: UploadFile = File(..., description="Screenshot image file (PNG/JPG/WEBP)"),
    description: Optional[str] = Form(None, description="Optional context"),
):
    pipeline = _get_pipeline()

    # Read the uploaded file into memory
    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    return await pipeline.verify_image(image_bytes, description=description)


# ── UC-03: URL Verification ──────────────────────────────────
@router.post(
    "/url",
    response_model=VerifyResponse,
    summary="Verify a news article URL",
)
async def verify_url(body: URLVerifyRequest):
    pipeline = _get_pipeline()
    return await pipeline.verify_url(str(body.url))
