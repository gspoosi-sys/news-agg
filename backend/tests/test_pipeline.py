"""Tests for the AI pipeline with mocked Gemini and Claude responses."""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.ai.pipeline import (
    process_article,
    should_include_in_feed,
    should_include_in_need_to_know,
)


def _make_anthropic_mock(category: str, sentiment: float, tldr: str, keep: bool = True):
    content_block = MagicMock()
    content_block.text = json.dumps(
        {"category": category, "sentiment_score": sentiment, "tldr": tldr, "keep": keep}
    )
    mock_message = MagicMock()
    mock_message.content = [content_block]
    return mock_message


def _make_gemini_mock(category: str, sentiment: float, tldr: str, keep: bool = True):
    mock_response = MagicMock()
    mock_response.text = json.dumps(
        {"category": category, "sentiment_score": sentiment, "tldr": tldr, "keep": keep}
    )
    return mock_response


@patch("app.ai.pipeline.settings")
@patch("app.ai.pipeline._get_anthropic_client")
def test_process_article_anthropic_positive(mock_get_client, mock_settings):
    mock_settings.gemini_api_key = ""
    mock_settings.anthropic_api_key = "fake_key"
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.messages.create.return_value = _make_anthropic_mock(
        "positive", 0.8, "Scientists make breakthrough in renewable energy."
    )

    result = process_article("Solar breakthrough", "New panels achieve 50% efficiency")
    assert result["category"] == "positive"
    assert result["sentiment_score"] == 0.8
    assert result["keep"] is True
    assert "breakthrough" in result["tldr"]


@patch("app.ai.pipeline.settings")
@patch("app.ai.pipeline._get_gemini_client")
def test_process_article_gemini_positive(mock_get_client, mock_settings):
    mock_settings.gemini_api_key = "fake_gemini_key"
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.models.generate_content.return_value = _make_gemini_mock(
        "positive", 0.8, "Scientists make breakthrough in renewable energy."
    )

    result = process_article("Solar breakthrough", "New panels achieve 50% efficiency")
    assert result["category"] == "positive"
    assert result["sentiment_score"] == 0.8
    assert result["keep"] is True
    assert "breakthrough" in result["tldr"]


@patch("app.ai.pipeline.settings")
@patch("app.ai.pipeline._get_gemini_client")
def test_process_article_gemini_political(mock_get_client, mock_settings):
    mock_settings.gemini_api_key = "fake_gemini_key"
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.models.generate_content.return_value = _make_gemini_mock(
        "political", -0.1, "World leaders met to discuss trade policy."
    )

    result = process_article("G7 Summit", "Leaders discuss global trade")
    assert result["category"] == "political"
    assert result["keep"] is True


@patch("app.ai.pipeline.settings")
@patch("app.ai.pipeline._get_gemini_client")
def test_process_article_gemini_discards_clickbait(mock_get_client, mock_settings):
    mock_settings.gemini_api_key = "fake_gemini_key"
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.models.generate_content.return_value = _make_gemini_mock(
        "neutral", 0.0, "", keep=False
    )

    result = process_article("You Won't BELIEVE This!", "Sponsored content")
    assert result["keep"] is False


@patch("app.ai.pipeline.settings")
@patch("app.ai.pipeline._get_gemini_client")
def test_process_article_falls_back_on_bad_json(mock_get_client, mock_settings):
    mock_settings.gemini_api_key = "fake_gemini_key"
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "not json at all"
    mock_client.models.generate_content.return_value = mock_response

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
