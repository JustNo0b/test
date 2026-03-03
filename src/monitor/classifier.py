"""AI-powered ad classifier — uses OpenAI to determine if a post is advertising."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

if TYPE_CHECKING:
    from src.monitor.database import Database

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Ты — эксперт по анализу контента телеграм-каналов.

Твоя задача — определить, является ли пост РЕКЛАМОЙ или КОНТЕНТОМ (полезным постом).

Признаки РЕКЛАМЫ:
- Прямая реклама товаров, услуг, курсов
- Партнёрские интеграции (упоминание промокодов, спец-ссылок)
- Пост написан в рекламном стиле с призывом купить/подписаться на сторонний ресурс
- «Нативная» реклама — полезный контент, но с явной целью продвижения чужого продукта
- Розыгрыши и конкурсы от спонсоров
- Репосты рекламных каналов

Признаки КОНТЕНТА:
- Авторские мысли, аналитика, мнения
- Обзоры индустрии без рекламных ссылок
- Образовательный контент
- Новости и дайджесты без коммерческой подоплёки
- Личные истории автора

Ответь строго в формате JSON:
{"is_ad": true/false, "confidence": 0.0-1.0, "reason": "краткое объяснение на русском"}
"""


class AdClassifier:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def classify(self, text: str) -> dict:
        """Classify a single post. Returns dict with is_ad, confidence, reason."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text[:4000]},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=200,
            )
            result = json.loads(response.choices[0].message.content)  # type: ignore[arg-type]
            return {
                "is_ad": bool(result.get("is_ad", False)),
                "confidence": float(result.get("confidence", 0.5)),
                "reason": result.get("reason", ""),
            }
        except Exception:
            logger.exception("Classification failed for post")
            return {"is_ad": False, "confidence": 0.0, "reason": "error"}

    async def classify_unprocessed(self, db: Database) -> int:
        """Classify all unprocessed posts in the database. Returns count processed."""
        posts = await db.get_unclassified_posts()
        classified = 0

        for post in posts:
            post_id = post["id"]
            text = post["text"]
            if not text or len(text.strip()) < 20:
                await db.update_ad_flag(post_id, is_ad=False, confidence=0.9)
                classified += 1
                continue

            result = await self.classify(text)
            await db.update_ad_flag(
                post_id,
                is_ad=result["is_ad"],
                confidence=result["confidence"],
            )
            classified += 1

            if result["is_ad"]:
                logger.info(
                    "Post #%d classified as AD (%.0f%%): %s",
                    post_id,
                    result["confidence"] * 100,
                    result["reason"],
                )

        logger.info("Classified %d posts", classified)
        return classified
