"""Telegram channel scraper — fetches posts for a given date range."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from telethon import TelegramClient
from telethon.tl.types import (
    MessageMediaDocument,
    MessageMediaPhoto,
    MessageMediaWebPage,
)

if TYPE_CHECKING:
    from src.monitor.database import Database

logger = logging.getLogger(__name__)


def _media_type(media: object) -> str | None:
    if isinstance(media, MessageMediaPhoto):
        return "photo"
    if isinstance(media, MessageMediaDocument):
        return "document"
    if isinstance(media, MessageMediaWebPage):
        return "webpage"
    return None


def _total_reactions(message) -> int:
    if message.reactions and message.reactions.results:
        return sum(r.count for r in message.reactions.results)
    return 0


class TelegramScraper:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_path: str,
    ) -> None:
        self.client = TelegramClient(session_path, api_id, api_hash)

    async def start(self) -> None:
        await self.client.start()
        logger.info("Telegram client connected")

    async def stop(self) -> None:
        await self.client.disconnect()

    async def scrape_channel(
        self,
        channel_username: str,
        db: Database,
        date_from: datetime,
        date_to: datetime,
    ) -> int:
        """Scrape posts from a channel for the given date range.
        Returns count of new posts saved.
        """
        entity = await self.client.get_entity(channel_username)
        channel_title = getattr(entity, "title", channel_username)
        channel_id = await db.upsert_channel(channel_username, channel_title)

        new_count = 0
        async for message in self.client.iter_messages(
            entity,
            offset_date=date_to,
            reverse=False,
        ):
            msg_date = message.date.replace(tzinfo=timezone.utc)
            if msg_date < date_from:
                break
            if msg_date >= date_to:
                continue

            text = message.text or message.raw_text or ""
            if not text and not message.media:
                continue

            url = f"https://t.me/{channel_username}/{message.id}"
            saved = await db.insert_post(
                channel_id=channel_id,
                tg_message_id=message.id,
                text=text if text else None,
                date=msg_date.isoformat(),
                views=message.views or 0,
                forwards=message.forwards or 0,
                reactions_count=_total_reactions(message),
                media_type=_media_type(message.media),
                url=url,
            )
            if saved:
                new_count += 1

        logger.info(
            "Channel @%s: %d new posts (%s — %s)",
            channel_username,
            new_count,
            date_from.date(),
            date_to.date(),
        )
        return new_count
