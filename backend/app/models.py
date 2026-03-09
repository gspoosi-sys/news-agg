from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI-generated fields
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="neutral")
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tldr: Mapped[str] = mapped_column(Text, nullable=False, default="")

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("url", name="uq_articles_url"),
        Index("ix_articles_category", "category"),
        Index("ix_articles_published_at", "published_at"),
        Index("ix_articles_sentiment_score", "sentiment_score"),
    )
