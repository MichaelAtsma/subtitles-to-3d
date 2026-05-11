from __future__ import annotations

import pysubs2

from src.core.converter import convert_subtitles_to_mode
from src.core.models import ConversionMode, ConversionSettings, Resolution, ResolutionMode


def _build_subs() -> pysubs2.SSAFile:
    subs = pysubs2.SSAFile()
    style = pysubs2.SSAStyle()
    style.alignment = 2
    style.marginl = 20
    style.marginr = 20
    style.marginv = 60
    subs.styles["Default"] = style
    subs.events.append(pysubs2.SSAEvent(start=0, end=1000, text="Hello world", style="Default"))
    return subs


def _settings() -> ConversionSettings:
    return ConversionSettings(
        conversion_mode=ConversionMode.ALL,
        resolution_mode=ResolutionMode.STANDARD,
        horizontal_offset=0,
        vertical_offset=0,
        pop_out=0,
    )


def test_hsbs_applies_horizontal_squeeze() -> None:
    subs = _build_subs()
    converted = convert_subtitles_to_mode(subs, Resolution(1920, 1080), _settings(), ConversionMode.HSBS)

    assert len(converted.events) == 2
    assert "\\fscx50" in converted.events[0].text
    assert "\\fscy50" not in converted.events[0].text


def test_hou_applies_vertical_squeeze() -> None:
    subs = _build_subs()
    converted = convert_subtitles_to_mode(subs, Resolution(1920, 1080), _settings(), ConversionMode.HOU)

    assert len(converted.events) == 2
    assert "\\fscy50" in converted.events[0].text
    assert "\\fscx50" not in converted.events[0].text


def test_fsbs_does_not_apply_squeeze() -> None:
    subs = _build_subs()
    converted = convert_subtitles_to_mode(subs, Resolution(3840, 1080), _settings(), ConversionMode.FSBS)

    assert len(converted.events) == 2
    assert "\\fscx50" not in converted.events[0].text
    assert "\\fscy50" not in converted.events[0].text


def test_hsbs_preserves_stronger_existing_x_scale() -> None:
    subs = _build_subs()
    subs.events[0].text = "{\\fscx30}Hello world"

    converted = convert_subtitles_to_mode(subs, Resolution(1920, 1080), _settings(), ConversionMode.HSBS)

    assert len(converted.events) == 2
    assert "\\fscx30" in converted.events[0].text


def test_positive_vertical_offset_moves_text_up() -> None:
    subs = _build_subs()
    settings = ConversionSettings(
        conversion_mode=ConversionMode.ALL,
        resolution_mode=ResolutionMode.STANDARD,
        vertical_offset=40,
    )

    converted = convert_subtitles_to_mode(subs, Resolution(1920, 1080), settings, ConversionMode.HSBS)

    assert len(converted.events) == 2
    assert "\\pos(480,980)" in converted.events[0].text
