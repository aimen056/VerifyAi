"""
VerifyAI — FastAPI Application Entry Point

Initialises the ML pipeline on startup and shuts it down gracefully.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import verify, health
from app.services.pipeline import VerificationPipeline
from app.services.classifier import RoBERTaClassifier
from app.services.processor import TesseractProcessor
from app.services.fact_checker import GoogleFactChecker
from app.services.explainer import ShapExplainer
from app.services.search_verifier import SearchVerifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


# ── Lifespan: load / unload ML pipeline ──────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the verification pipeline on startup."""
    logger.info("🚀 Starting VerifyAI pipeline initialisation …")

    pipeline = VerificationPipeline(
        classifier=RoBERTaClassifier(
            model_name=settings.ml_model_name,
            device=settings.ml_device,
            max_length=settings.ml_max_length,
        ),
        processor=TesseractProcessor(
            tesseract_cmd=settings.tesseract_cmd,
            language=settings.tesseract_lang,
        ),
        fact_checker=GoogleFactChecker(
            api_key=settings.google_factcheck_api_key,
            language_code=settings.factcheck_language,
            max_results=settings.factcheck_max_results,
        ),
        explainer=ShapExplainer(
            max_tokens_display=settings.shap_max_tokens,
            timeout_seconds=settings.shap_timeout_seconds,
        ),
        search_verifier=SearchVerifier(
            google_api_key=settings.custom_search_api,
            google_cx=settings.custom_search_engine_id,
            serper_api_key=settings.serper_api,
            groq_api_key=settings.groq_api_key,
        ),
    )

    try:
        await pipeline.initialise()
        logger.info("✅ Verification pipeline ready.")
    except Exception as e:
        logger.error(f"⚠️  Pipeline initialisation failed: {e}", exc_info=True)
        logger.info("Server will start, but /verify endpoints will return 503.")

    # Inject pipeline into the router
    verify.set_pipeline(pipeline)

    # Store on app.state so the health endpoint can read it
    app.state.pipeline = pipeline

    yield  # ← app runs here

    logger.info("🛑 Shutting down VerifyAI pipeline …")


# ── App Instance ──────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered Fake News & Screenshot Verification Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Middleware (Must be FIRST) ───────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Debug Logging Middleware ──────────────────────────────────
@app.middleware("http")
async def log_requests(request, call_next):
    try:
        logger.info(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR during request: {str(e)}", exc_info=True)
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(e)}"},
            headers={"Access-Control-Allow-Origin": "*"} # Force CORS on error
        )

# ── Routers ───────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(verify.router)

# ── Root ──────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
