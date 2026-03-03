"""Configuration loader — reads .env and provides typed settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class TelegramConfig:
    api_id: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash: str = os.getenv("TELEGRAM_API_HASH", "")
    phone: str = os.getenv("TELEGRAM_PHONE", "")
    session_path: str = str(PROJECT_ROOT / "storage" / "tg.session")


@dataclass(frozen=True)
class AppConfig:
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    database_path: str = os.getenv(
        "DATABASE_PATH", str(PROJECT_ROOT / "storage" / "content.db")
    )
    channels_file: str = str(PROJECT_ROOT / "channels.yml")
    monitor_output_dir: str = str(PROJECT_ROOT / "storage" / "monitor")


def get_config() -> AppConfig:
    return AppConfig()
