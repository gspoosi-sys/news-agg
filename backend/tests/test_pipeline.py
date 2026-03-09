"""Tests for the AI pipeline with mocked Claude responses."""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.ai.pipeline import (
    process_article,
    should_include_in_feed,
    should_include_in_need_to_know,
)


def _make_mock_response(category: str, sentiment: float, tldr: str, keep: bool = True):
    content_block = MagicMock()
    content_block.text = json.dumps(
        {"category": category, "sentiment_score": sentiment, "tldr": tldr, "keep": keep}
    )
    mock_message = MagicMock()
    mock_message.content = [content_block]
    return mock_message


@patch("app.ai.pipeline._get_client")
def test_process_article_positive(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        "positive", 0.8, "Scientists make breakthrough in renewable energy."
    )

    result = process_article("Solar breakthrough", "New panels achieve 50% efficiency")
    assert result["category"] == "positive"
    assert result["sentiment_score"] == 0.8
    assert result["keep"] is True
    assert "breakthrough" in result["tldr"]


@patch("app.ai.pipeline._get_client")
def test_process_article_political(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        "political", -0.1, "World leaders met to discuss trade policy."
    )

    result = process_article("G7 Summit", "Leaders discuss global trade")
    assert result["category"] == "political"
    assert result["keep"] is True


@patch("app.ai.pipeline._get_client")
def test_process_article_discards_clickbait(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        "neutral", 0.0, "", keep=False
    )

    result = process_article("You Won't BELIEVE This!", "Sponsored content")
    assert result["keep"] is False


@patch("app.ai.pipeline._get_client")
def test_process_article_falls_back_on_bad_json(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    content_block = MagicMock()
    content_block.text = "not json at all"
    mock_message = MagicMock()
    mock_message.content = [content_block]
    mock_client.messages.create.return_value = mock_message

    result = process_article("Some title", "Some description")
    assert result["category"] == "neutral"
    assert result["keep"] is True


def test_should_include_in_feed():
    assert should_include_in_feed("positive", 0.5) is True
    assert should_include_in_feed("positive", 0.1) is False  # below threshold
    assert should_include_in_feed("neutral", 0.4) is True
    assert should_include_in_feed("political", 0.9) is False
    assert should_include_in_feed("negative", 0.8) is False


def test_should_include_in_need_to_know():
    assert should_include_in_need_to_know("political") is True
    assert should_include_in_need_to_know("positive") is False
    assert should_include_in_need_to_know("negative") is False
