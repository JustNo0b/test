"""Tests for the ad classifier (unit tests with mocked OpenAI)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.monitor.classifier import AdClassifier


@pytest.fixture
def mock_openai_response():
    def _make(is_ad: bool, confidence: float, reason: str):
        response = MagicMock()
        choice = MagicMock()
        choice.message.content = json.dumps(
            {"is_ad": is_ad, "confidence": confidence, "reason": reason}
        )
        response.choices = [choice]
        return response
    return _make


@pytest.mark.asyncio
async def test_classify_content(mock_openai_response):
    classifier = AdClassifier(api_key="test-key")

    with patch.object(
        classifier._client.chat.completions,
        "create",
        new_callable=AsyncMock,
        return_value=mock_openai_response(False, 0.92, "авторский контент"),
    ):
        result = await classifier.classify("Вот мои мысли о развитии AI в 2025 году...")

    assert result["is_ad"] is False
    assert result["confidence"] > 0.9


@pytest.mark.asyncio
async def test_classify_ad(mock_openai_response):
    classifier = AdClassifier(api_key="test-key")

    with patch.object(
        classifier._client.chat.completions,
        "create",
        new_callable=AsyncMock,
        return_value=mock_openai_response(True, 0.95, "рекламная интеграция"),
    ):
        result = await classifier.classify(
            "Промокод SAVE20 для скидки на курс по Python! Переходите по ссылке..."
        )

    assert result["is_ad"] is True
    assert result["confidence"] > 0.9


@pytest.mark.asyncio
async def test_classify_error_handling():
    classifier = AdClassifier(api_key="test-key")

    with patch.object(
        classifier._client.chat.completions,
        "create",
        new_callable=AsyncMock,
        side_effect=Exception("API error"),
    ):
        result = await classifier.classify("Some text")

    assert result["is_ad"] is False
    assert result["confidence"] == 0.0
    assert result["reason"] == "error"
