from __future__ import annotations

from pathlib import Path

import pysubs2

SUPPORTED_EXTENSIONS = {".srt", ".ass", ".vtt"}


class SubtitleParseError(RuntimeError):
    pass


def validate_subtitle_path(subtitle_path: Path) -> None:
    if not subtitle_path.exists() or not subtitle_path.is_file():
        raise SubtitleParseError(f"Subtitle file does not exist: {subtitle_path}")

    suffix = subtitle_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise SubtitleParseError(
            f"Unsupported subtitle format '{suffix}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )


def load_subtitles(subtitle_path: Path) -> pysubs2.SSAFile:
    validate_subtitle_path(subtitle_path)
    try:
        return pysubs2.load(str(subtitle_path))
    except Exception as exc:
        raise SubtitleParseError(f"Unable to parse subtitle file '{subtitle_path.name}': {exc}") from exc
