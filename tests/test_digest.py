"""Tests for the digest generator."""

from datetime import date

import pytest
import pytest_asyncio

from src.monitor.database import Database
from src.monitor.digest import DigestGenerator


@pytest_asyncio.fixture
async def db_with_posts(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    await db.connect()

    ch_id = await db.upsert_channel("ai_channel", "AI News")
    for i in range(5):
        await db.insert_post(
            channel_id=ch_id,
            tg_message_id=i + 1,
            text=f"Пост #{i + 1} о технологиях искусственного интеллекта",
            date=f"2025-01-{5 + i:02d}T10:00:00",
            views=100 * (i + 1),
            forwards=i * 2,
            reactions_count=i * 5,
            media_type=None,
            url=f"https://t.me/ai_channel/{i + 1}",
        )

    yield db
    await db.close()


@pytest.mark.asyncio
async def test_generate_digest(db_with_posts, tmp_path):
    output_dir = str(tmp_path / "digests")
    generator = DigestGenerator(output_dir)
    path = await generator.generate(
        db_with_posts,
        week_start=date(2025, 1, 1),
        week_end=date(2025, 1, 10),
    )

    assert path.endswith(".html")
    with open(path, encoding="utf-8") as f:
        html = f.read()

    assert "Еженедельный дайджест" in html
    assert "@ai_channel" in html
    assert "5" in html


@pytest.mark.asyncio
async def test_empty_digest(tmp_path):
    db = Database(str(tmp_path / "empty.db"))
    await db.connect()

    output_dir = str(tmp_path / "digests")
    generator = DigestGenerator(output_dir)
    path = await generator.generate(
        db,
        week_start=date(2025, 1, 1),
        week_end=date(2025, 1, 7),
    )

    assert path.endswith(".html")
    with open(path, encoding="utf-8") as f:
        html = f.read()

    assert "0" in html
    await db.close()
