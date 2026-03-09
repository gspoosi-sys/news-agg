"""AI pipeline: uses Claude API to categorize articles and generate TL;DR summaries."""
import json
import logging

import anthropic
from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

_anthropic_client: anthropic.Anthropic | None = None
_gemini_client: genai.Client | None = None

SYSTEM_PROMPT = """You are a news editor for a balanced, calm news service designed to combat doom-scrolling.

Analyze the article title and description and return ONLY valid JSON with exactly these fields:
- "category": one of "political", "positive", "neutral", "negative"
  - "political": major political, governmental, geopolitical, or conflict events
  - "positive": uplifting, solution-oriented, scientific breakthrough, human interest, environmental progress
  - "negative": crime, disaster, tragedy, controversy without constructive angle
  - "neutral": general news that doesn't strongly fit other categories
- "sentiment_score": float from -1.0 (very negative) to 1.0 (very positive)
- "tldr": 1-2 sentence objective, calm summary. No sensationalism, no alarming language. State facts plainly.
- "keep": true if the article is substantive news; false if it is an advertisement, clickbait, listicle, or fluff

Return ONLY the JSON object, no markdown, no extra text."""


def _get_anthropic_client() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def _get_gemini_client() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.gemini_api_key)
    return _gemini_client


def _process_with_gemini(title: str, description: str) -> dict:
    client = _get_gemini_client()
    user_content = f"Title: {title}\n\nDescription: {description or '(no description)'}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            )
        )
        raw = response.text.strip()
        result = json.loads(raw)
        return _build_result(result, title)
    except Exception as e:
        logger.error("Gemini API error for article '%s': %s", title, e)
        return _fallback_result(title)


def _process_with_anthropic(title: str, description: str) -> dict:
    client = _get_anthropic_client()
    user_content = f"Title: {title}\n\nDescription: {description or '(no description)'}"

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = message.content[0].text.strip()
        result = json.loads(raw)
        return _build_result(result, title)
    except Exception as e:
        logger.error("Claude API error for article '%s': %s", title, e)
        return _fallback_result(title)


def _build_result(result: dict, title: str) -> dict:
    return {
        "category": result.get("category", "neutral"),
        "sentiment_score": float(result.get("sentiment_score", 0.0)),
        "tldr": result.get("tldr", title),
        "keep": bool(result.get("keep", True)),
    }


def _fallback_result(title: str) -> dict:
    return {"category": "neutral", "sentiment_score": 0.0, "tldr": title, "keep": True}


def process_article(title: str, description: str) -> dict:
    """Run a single article through the AI pipeline (Gemini or Claude).

    Returns a dict with keys: category, sentiment_score, tldr, keep.
    Falls back to safe defaults on any error.
    """
    if settings.gemini_api_key:
        return _process_with_gemini(title, description)
    elif settings.anthropic_api_key:
        return _process_with_anthropic(title, description)
    else:
        logger.warning("No AI API key configured! Falling back to safe defaults for '%s'", title)
        return _fallback_result(title)


def should_include_in_feed(category: str, sentiment_score: float) -> bool:
    """Determine if a categorized article belongs in the positive main feed."""
    if category == "positive" and sentiment_score >= 0.2:
        return True
    if category == "neutral" and sentiment_score >= 0.4:
        return True
    return False


def should_include_in_need_to_know(category: str) -> bool:
    """Determine if an article belongs in the Need to Know political section."""
    return category == "political"
