"""SQLite storage for scraped posts and classification results."""

from __future__ import annotations

import aiosqlite
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    title       TEXT,
    added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      INTEGER NOT NULL REFERENCES channels(id),
    tg_message_id   INTEGER NOT NULL,
    text            TEXT,
    date            TIMESTAMP NOT NULL,
    views           INTEGER DEFAULT 0,
    forwards        INTEGER DEFAULT 0,
    reactions_count INTEGER DEFAULT 0,
    media_type      TEXT,
    url             TEXT,
    is_ad           BOOLEAN,
    ad_confidence   REAL,
    scraped_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, tg_message_id)
);

CREATE TABLE IF NOT EXISTS digests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start  DATE NOT NULL,
    week_end    DATE NOT NULL,
    html_path   TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date);
CREATE INDEX IF NOT EXISTS idx_posts_is_ad ON posts(is_ad);
"""


class Database:
    def __init__(self, db_path: str) -> None:
        self._path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        assert self._conn is not None, "Database not connected"
        return self._conn

    async def upsert_channel(self, username: str, title: str | None = None) -> int:
        await self.conn.execute(
            "INSERT OR IGNORE INTO channels (username, title) VALUES (?, ?)",
            (username, title),
        )
        await self.conn.commit()
        cursor = await self.conn.execute(
            "SELECT id FROM channels WHERE username = ?", (username,)
        )
        row = await cursor.fetchone()
        return row[0]  # type: ignore[index]

    async def insert_post(
        self,
        channel_id: int,
        tg_message_id: int,
        text: str | None,
        date: str,
        views: int,
        forwards: int,
        reactions_count: int,
        media_type: str | None,
        url: str | None,
    ) -> bool:
        """Insert a post. Returns True if new, False if duplicate."""
        try:
            await self.conn.execute(
                """INSERT INTO posts
                   (channel_id, tg_message_id, text, date, views, forwards,
                    reactions_count, media_type, url)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    channel_id,
                    tg_message_id,
                    text,
                    date,
                    views,
                    forwards,
                    reactions_count,
                    media_type,
                    url,
                ),
            )
            await self.conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def update_ad_flag(
        self, post_id: int, is_ad: bool, confidence: float
    ) -> None:
        await self.conn.execute(
            "UPDATE posts SET is_ad = ?, ad_confidence = ? WHERE id = ?",
            (is_ad, confidence, post_id),
        )
        await self.conn.commit()

    async def get_unclassified_posts(self) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(
            "SELECT id, text, url FROM posts WHERE is_ad IS NULL AND text IS NOT NULL"
        )
        return await cursor.fetchall()

    async def get_posts_for_period(
        self, start_date: str, end_date: str, only_content: bool = True
    ) -> list[aiosqlite.Row]:
        query = """
            SELECT p.*, c.username as channel_username, c.title as channel_title
            FROM posts p
            JOIN channels c ON c.id = p.channel_id
            WHERE p.date >= ? AND p.date < ?
        """
        if only_content:
            query += " AND (p.is_ad = 0 OR p.is_ad IS NULL)"
        query += " ORDER BY p.date DESC"
        cursor = await self.conn.execute(query, (start_date, end_date))
        return await cursor.fetchall()

    async def save_digest(
        self, week_start: str, week_end: str, html_path: str
    ) -> int:
        cursor = await self.conn.execute(
            "INSERT INTO digests (week_start, week_end, html_path) VALUES (?, ?, ?)",
            (week_start, week_end, html_path),
        )
        await self.conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]
