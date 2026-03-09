from datetime import datetime

from pydantic import BaseModel


class ArticleSummary(BaseModel):
    id: int
    title: str
    source: str
    url: str
    image_url: str | None
    category: str
    sentiment_score: float
    tldr: str
    published_at: datetime | None

    model_config = {"from_attributes": True}


class ArticleDetail(ArticleSummary):
    description: str | None


class FeedResponse(BaseModel):
    articles: list[ArticleSummary]
    total: int
    page: int
    limit: int


class NeedToKnowResponse(BaseModel):
    articles: list[ArticleSummary]


class RefreshResponse(BaseModel):
    status: str
    message: str
