"""Ingestion scheduler: fetches, deduplicates, processes, and stores articles."""
import logging

from sqlalchemy.exc import IntegrityError

from app.ai.pipeline import process_article, should_include_in_feed, should_include_in_need_to_know
from app.config import settings
from app.database import SessionLocal
from app.ingestion.deduplicator import is_seen, mark_seen
from app.ingestion.fetcher import fetch_all
from app.models import Article

logger = logging.getLogger(__name__)


def run_ingestion() -> dict:
    """Main ingestion job: fetch → deduplicate → AI pipeline → store."""
    logger.info("Starting ingestion run")
    articles = fetch_all()

    new_count = 0
    skipped_count = 0
    error_count = 0
    discarded_count = 0

    db = SessionLocal()
    try:
        for raw in articles:
            if not raw.url or not raw.title:
                skipped_count += 1
                continue

            if is_seen(raw.url):
                skipped_count += 1
                continue

            # Run through AI pipeline
            try:
                ai_result = process_article(raw.title, raw.description or "")
            except Exception as e:
                logger.error("AI pipeline error for '%s': %s", raw.title, e)
                error_count += 1
                continue

            # Filter: discard junk, ads, and extreme negativity
            if not ai_result["keep"]:
                discarded_count += 1
                mark_seen(raw.url)
                continue

            category = ai_result["category"]
            sentiment_score = ai_result["sentiment_score"]

            # Only store articles that will appear in a section
            if not (
                should_include_in_need_to_know(category)
                or should_include_in_feed(category, sentiment_score)
            ):
                discarded_count += 1
                mark_seen(raw.url)
                continue

            article = Article(
                url=raw.url,
                title=raw.title,
                source=raw.source,
                description=raw.description,
                image_url=raw.image_url,
                published_at=raw.published_at,
                category=category,
                sentiment_score=sentiment_score,
                tldr=ai_result["tldr"],
            )

            try:
                db.add(article)
                db.commit()
                mark_seen(raw.url)
                new_count += 1
            except IntegrityError:
                db.rollback()
                mark_seen(raw.url)
                skipped_count += 1
            except Exception as e:
                db.rollback()
                logger.error("DB error saving article '%s': %s", raw.title, e)
                error_count += 1
    finally:
        db.close()

    summary = {
        "new": new_count,
        "skipped": skipped_count,
        "discarded": discarded_count,
        "errors": error_count,
    }
    logger.info("Ingestion complete: %s", summary)
    return summary
