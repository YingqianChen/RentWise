"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .api.v1 import api_router
from .core.config import settings
from .db.database import get_engine
from .services.ocr_service import OCRService


app = FastAPI(
    title="RentWise API",
    description="API for RentWise - Hong Kong Rental Research Agent",
    version="1.0.0",
)

logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def warmup_services() -> None:
    """Warm expensive services during startup so the first user request is faster."""
    if settings.effective_ocr_prewarm_on_startup:
        try:
            await OCRService().warmup()
            logger.info("%s engine warmed up during startup", settings.OCR_PROVIDER)
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("%s warmup skipped: %s", settings.OCR_PROVIDER, exc)


@app.get("/health")
async def health_check():
    """Health check endpoint — also verifies the database connection."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "environment": settings.APP_ENV}
    except Exception as exc:
        logger.error("Health check failed — database unreachable: %s", exc)
        return {"status": "unhealthy", "database": "disconnected", "error": str(exc)}
