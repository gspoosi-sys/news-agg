"""FastAPI application entry point."""
import logging
import logging.config

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Balanced News Aggregator API",
    description="Curated news feed with AI-generated TL;DR summaries",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)

_scheduler: BackgroundScheduler | None = None


@app.on_event("startup")
def startup() -> None:
    global _scheduler

    # Run an initial ingestion on startup
    from app.ingestion.scheduler import run_ingestion

    logger.info("Running initial ingestion on startup…")
    try:
        run_ingestion()
    except Exception as e:
        logger.warning("Initial ingestion failed (will retry on schedule): %s", e)

    # Schedule recurring ingestion
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        run_ingestion,
        "interval",
        minutes=settings.ingestion_interval_minutes,
        id="ingestion",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started — ingestion every %d min", settings.ingestion_interval_minutes)


@app.on_event("shutdown")
def shutdown() -> None:
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
