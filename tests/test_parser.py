from __future__ import annotations

from pathlib import Path

import pytest

from src.core.parser import SubtitleParseError, load_subtitles


def test_loads_srt_file(tmp_path: Path) -> None:
    subtitle = tmp_path / "sample.srt"
    subtitle.write_text(
        "1\n"
        "00:00:00,000 --> 00:00:01,000\n"
        "Hello\n",
        encoding="utf-8",
    )

    loaded = load_subtitles(subtitle)
    assert len(loaded.events) == 1


def test_rejects_unsupported_extension(tmp_path: Path) -> None:
    subtitle = tmp_path / "sample.txt"
    subtitle.write_text("example", encoding="utf-8")

    with pytest.raises(SubtitleParseError):
        load_subtitles(subtitle)
