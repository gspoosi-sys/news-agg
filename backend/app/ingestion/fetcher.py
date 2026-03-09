"""Fetches articles from NewsAPI and RSS feeds."""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RawArticle:
    title: str
    url: str
    source: str
    description: str | None
    image_url: str | None
    published_at: datetime | None


RSS_FEEDS = [
    # General / Geopolitical
    ("BBC News", "http://feeds.bbci.co.uk/news/rss.xml"),
    ("Reuters", "https://feeds.reuters.com/reuters/topNews"),
    ("AP News", "https://rsshub.app/apnews/topics/ap-top-news"),
    # Positive / Solutions-focused
    ("Good News Network", "https://www.goodnewsnetwork.org/feed/"),
    ("Positive News", "https://www.positive.news/feed/"),
    ("Solutions Journalism", "https://thewholestory.solutionsjournalism.org/feed"),
]


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    import email.utils

    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


def fetch_rss_feeds() -> list[RawArticle]:
    articles: list[RawArticle] = []

    for source_name, feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                url = entry.get("link", "")
                title = entry.get("title", "").strip()
                if not url or not title:
                    continue

                description = entry.get("summary", None) or entry.get("description", None)
                if description:
                    # Strip HTML tags crudely
                    import re
                    description = re.sub(r"<[^>]+>", "", description).strip()[:1000]

                image_url = None
                if hasattr(entry, "media_content") and entry.media_content:
                    image_url = entry.media_content[0].get("url")
                elif hasattr(entry, "enclosures") and entry.enclosures:
                    for enc in entry.enclosures:
                        if enc.get("type", "").startswith("image/"):
                            image_url = enc.get("href")
                            break

                articles.append(
                    RawArticle(
                        title=title,
                        url=url,
                        source=source_name,
                        description=description,
                        image_url=image_url,
                        published_at=_parse_date(entry.get("published")),
                    )
                )
        except Exception as e:
            logger.warning("Failed to fetch RSS feed '%s': %s", feed_url, e)

    logger.info("Fetched %d articles from RSS feeds", len(articles))
    return articles


def fetch_newsapi() -> list[RawArticle]:
    if not settings.news_api_key:
        logger.info("NEWS_API_KEY not set — skipping NewsAPI")
        return []

    articles: list[RawArticle] = []
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://newsapi.org/v2/top-headlines",
                params={
                    "apiKey": settings.news_api_key,
                    "language": "en",
                    "pageSize": 30,
                },
            )
            response.raise_for_status()
            data = response.json()

        for item in data.get("articles", []):
            url = item.get("url", "")
            title = (item.get("title") or "").strip()
            if not url or not title or url == "https://removed.com":
                continue

            published_at = None
            if raw_date := item.get("publishedAt"):
                try:
                    published_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).replace(
                        tzinfo=None
                    )
                except ValueError:
                    pass

            source_name = item.get("source", {}).get("name") or "NewsAPI"
            articles.append(
                RawArticle(
                    title=title,
                    url=url,
                    source=source_name,
                    description=item.get("description"),
                    image_url=item.get("urlToImage"),
                    published_at=published_at,
                )
            )
    except httpx.HTTPError as e:
        logger.warning("NewsAPI request failed: %s", e)

    logger.info("Fetched %d articles from NewsAPI", len(articles))
    return articles


def fetch_guardian() -> list[RawArticle]:
    if not settings.guardian_api_key:
        logger.info("GUARDIAN_API_KEY not set — skipping The Guardian")
        return []

    articles: list[RawArticle] = []
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://content.guardianapis.com/search",
                params={
                    "api-key": settings.guardian_api_key,
                    "show-fields": "thumbnail,trailText",
                    "page-size": 20,
                    "order-by": "newest",
                },
            )
            response.raise_for_status()
            data = response.json()

        for item in data.get("response", {}).get("results", []):
            url = item.get("webUrl", "")
            title = item.get("webTitle", "").strip()
            if not url or not title:
                continue

            fields = item.get("fields", {})
            published_at = None
            if raw_date := item.get("webPublicationDate"):
                try:
                    published_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).replace(
                        tzinfo=None
                    )
                except ValueError:
                    pass

            articles.append(
                RawArticle(
                    title=title,
                    url=url,
                    source="The Guardian",
                    description=fields.get("trailText"),
                    image_url=fields.get("thumbnail"),
                    published_at=published_at,
                )
            )
    except httpx.HTTPError as e:
        logger.warning("Guardian API request failed: %s", e)

    logger.info("Fetched %d articles from The Guardian", len(articles))
    return articles


def fetch_all() -> list[RawArticle]:
    """Fetch from all configured sources and return combined list."""
    results: list[RawArticle] = []
    results.extend(fetch_rss_feeds())
    results.extend(fetch_newsapi())
    results.extend(fetch_guardian())
    logger.info("Total articles fetched: %d", len(results))
    return results
