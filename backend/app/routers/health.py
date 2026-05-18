"""
Health-check endpoint — used by Docker, load balancers, and the frontend
to confirm the backend is alive and report pipeline readiness.
"""

from fastapi import APIRouter, Request
from app.models import HealthResponse
from app.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check(request: Request):
    settings = get_settings()

    # Check pipeline status from app.state (set by lifespan)
    pipeline = getattr(request.app.state, "pipeline", None)
    pipeline_status = "not_loaded"
    if pipeline is not None:
        if pipeline.is_ready:
            pipeline_status = "ready"
        else:
            pipeline_status = "loading"

    return HealthResponse(
        status="ok",
        version=settings.app_version,
        services={
            "database": "not_connected",   # wired when DB is set up
            "redis": "not_connected",      # wired when Redis is set up
            "ml_pipeline": pipeline_status,
            "classifier": "loaded" if (pipeline and pipeline.classifier.is_loaded()) else "not_loaded",
            "shap_explainer": "ready" if (pipeline and pipeline.explainer.is_ready) else "not_ready",
            "ocr": "available",
            "fact_check_api": "configured" if settings.google_factcheck_api_key and settings.google_factcheck_api_key != "your_google_api_key_here" else "not_configured",
        },
    )
