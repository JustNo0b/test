"""Tests for the database module."""

import pytest
import pytest_asyncio

from src.monitor.database import Database


@pytest_asyncio.fixture
async def db(tmp_path):
    database = Database(str(tmp_path / "test.db"))
    await database.connect()
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_upsert_channel(db):
    ch_id = await db.upsert_channel("test_channel", "Test Channel")
    assert ch_id == 1

    ch_id2 = await db.upsert_channel("test_channel", "Test Channel")
    assert ch_id2 == 1  # same channel, same id


@pytest.mark.asyncio
async def test_insert_post(db):
    ch_id = await db.upsert_channel("test_channel")
    saved = await db.insert_post(
        channel_id=ch_id,
        tg_message_id=42,
        text="Hello, world!",
        date="2025-01-01T10:00:00",
        views=100,
        forwards=5,
        reactions_count=20,
        media_type=None,
        url="https://t.me/test_channel/42",
    )
    assert saved is True

    duplicate = await db.insert_post(
        channel_id=ch_id,
        tg_message_id=42,
        text="Hello, world!",
        date="2025-01-01T10:00:00",
        views=100,
        forwards=5,
        reactions_count=20,
        media_type=None,
        url="https://t.me/test_channel/42",
    )
    assert duplicate is False


@pytest.mark.asyncio
async def test_ad_classification(db):
    ch_id = await db.upsert_channel("test_channel")
    await db.insert_post(
        channel_id=ch_id,
        tg_message_id=1,
        text="Great AI article about transformers",
        date="2025-01-01T10:00:00",
        views=50,
        forwards=2,
        reactions_count=10,
        media_type=None,
        url="https://t.me/test_channel/1",
    )

    unclassified = await db.get_unclassified_posts()
    assert len(unclassified) == 1

    await db.update_ad_flag(unclassified[0]["id"], is_ad=False, confidence=0.95)
    unclassified = await db.get_unclassified_posts()
    assert len(unclassified) == 0


@pytest.mark.asyncio
async def test_get_posts_for_period(db):
    ch_id = await db.upsert_channel("channel1", "Channel One")
    await db.insert_post(
        channel_id=ch_id,
        tg_message_id=1,
        text="Content post",
        date="2025-01-05T10:00:00",
        views=100,
        forwards=5,
        reactions_count=10,
        media_type=None,
        url="https://t.me/channel1/1",
    )
    await db.update_ad_flag(1, is_ad=False, confidence=0.9)

    await db.insert_post(
        channel_id=ch_id,
        tg_message_id=2,
        text="Ad post — buy our product!",
        date="2025-01-06T10:00:00",
        views=200,
        forwards=0,
        reactions_count=2,
        media_type=None,
        url="https://t.me/channel1/2",
    )
    await db.update_ad_flag(2, is_ad=True, confidence=0.95)

    content_only = await db.get_posts_for_period("2025-01-01", "2025-01-10", only_content=True)
    assert len(content_only) == 1

    all_posts = await db.get_posts_for_period("2025-01-01", "2025-01-10", only_content=False)
    assert len(all_posts) == 2


@pytest.mark.asyncio
async def test_save_digest(db):
    digest_id = await db.save_digest("2025-01-01", "2025-01-07", "/tmp/digest.html")
    assert digest_id is not None
    assert digest_id > 0
