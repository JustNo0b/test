"""Tests for the channels loader."""

from src.monitor.channels import load_channels


def test_load_channels(tmp_path):
    yml = tmp_path / "channels.yml"
    yml.write_text(
        "channels:\n"
        "  - username: durov\n"
        "    tags: [tech]\n"
        "  - username: breakingmash\n"
        "    tags: [news]\n"
    )
    channels = load_channels(str(yml))
    assert len(channels) == 2
    assert channels[0]["username"] == "durov"


def test_load_empty_file(tmp_path):
    yml = tmp_path / "channels.yml"
    yml.write_text("channels: []\n")
    channels = load_channels(str(yml))
    assert channels == []


def test_load_missing_file():
    channels = load_channels("/nonexistent/path.yml")
    assert channels == []
