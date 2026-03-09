"""FastAPI route handlers."""
import json
import logging

import redis as redis_lib
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Article
from app.schemas import ArticleDetail, ArticleSummary, FeedResponse, NeedToKnowResponse, RefreshResponse

logger = logging.getLogger(__name__)
router = APIRouter()

_redis: redis_lib.Redis | None = None

CACHE_TTL = 300  # 5 minutes


def get_redis() -> redis_lib.Redis | None:
    global _redis
    if _redis is None:
        try:
            _redis = redis_lib.from_url(settings.redis_url, decode_responses=True)
            _redis.ping()
        except Exception:
            _redis = None
    return _redis


def _cache_get(key: str) -> dict | None:
    r = get_redis()
    if r is None:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _cache_set(key: str, data: dict) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        r.setex(key, CACHE_TTL, json.dumps(data))
    except Exception:
        pass


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/api/need-to-know", response_model=NeedToKnowResponse)
def need_to_know(db: Session = Depends(get_db)) -> NeedToKnowResponse:
    cache_key = "feed:need-to-know"
    cached = _cache_get(cache_key)
    if cached:
        return NeedToKnowResponse(**cached)

    rows = (
        db.query(Article)
        .filter(Article.category == "political")
        .order_by(desc(Article.published_at))
        .limit(settings.max_political_articles)
        .all()
    )

    result = NeedToKnowResponse(articles=[ArticleSummary.model_validate(r) for r in rows])
    _cache_set(cache_key, result.model_dump(mode="json"))
    return result


@router.get("/api/feed", response_model=FeedResponse)
def feed(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> FeedResponse:
    cache_key = f"feed:positive:p{page}:l{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return FeedResponse(**cached)

    offset = (page - 1) * limit
    base_query = db.query(Article).filter(
        Article.category.in_(["positive", "neutral"]),
        Article.sentiment_score >= 0.2,
    )

    total = base_query.with_entities(func.count()).scalar() or 0
    rows = (
        base_query
        .order_by(desc(Article.published_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = FeedResponse(
        articles=[ArticleSummary.model_validate(r) for r in rows],
        total=total,
        page=page,
        limit=limit,
    )
    _cache_set(cache_key, result.model_dump(mode="json"))
    return result


@router.get("/api/articles/{article_id}", response_model=ArticleDetail)
def article_detail(article_id: int, db: Session = Depends(get_db)) -> ArticleDetail:
    row = db.query(Article).filter(Article.id == article_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleDetail.model_validate(row)


@router.post("/api/refresh", response_model=RefreshResponse)
def refresh(
    background_tasks: BackgroundTasks,
    x_api_key: str | None = Header(default=None),
) -> RefreshResponse:
    if x_api_key != settings.refresh_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    from app.ingestion.scheduler import run_ingestion

    background_tasks.add_task(run_ingestion)
    return RefreshResponse(status="accepted", message="Ingestion job queued")
