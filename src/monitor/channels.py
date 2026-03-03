"""Channel list loader — reads channels.yml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_channels(filepath: str) -> list[dict[str, Any]]:
    """Load channel list from YAML file."""
    path = Path(filepath)
    if not path.exists():
        return []

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or not data.get("channels"):
        return []

    return data["channels"]
