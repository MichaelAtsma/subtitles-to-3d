from __future__ import annotations

import re

import pysubs2

from src.core.converter import Position, apply_overflow_strategy, apply_position_and_transform_override, count_overflowing_events
from src.core.models import ConversionMode, ConversionSettings, OverflowHandling, Resolution, ResolutionMode, SubtitleSize


def _style(fontsize: int = 40) -> pysubs2.SSAStyle:
    style = pysubs2.SSAStyle()
    style.alignment = 2
    style.marginl = 20
    style.marginr = 20
    style.marginv = 60
    style.fontsize = fontsize
    return style


def _event(text: str) -> pysubs2.SSAEvent:
    return pysubs2.SSAEvent(start=0, end=1000, text=text, style="Default")


def _settings(size: SubtitleSize = SubtitleSize.MEDIUM) -> ConversionSettings:
    return ConversionSettings(
        conversion_mode=ConversionMode.HSBS,
        resolution_mode=ResolutionMode.STANDARD,
        subtitle_size=size,
    )


def test_detects_side_by_side_overflow() -> None:
    subs = pysubs2.SSAFile()
    subs.styles["Default"] = _style(fontsize=52)
    subs.events.append(_event("This is a very long subtitle line that should overflow the half width for HSBS mode"))

    overflow = count_overflowing_events(subs, Resolution(1920, 1080), ConversionMode.HSBS, _settings())
    assert overflow == 1


def test_detects_overflow_after_effective_scaling() -> None:
    subs = pysubs2.SSAFile()
    subs.styles["Default"] = _style(fontsize=20)
    subs.events.append(_event("This subtitle line becomes too wide after conversion scaling and should be detected"))

    overflow = count_overflowing_events(
        subs,
        Resolution(1920, 1080),
        ConversionMode.HSBS,
        _settings(SubtitleSize.LARGE),
    )
    assert overflow == 1


def test_scale_down_strategy_adds_scale_tag() -> None:
    style = _style(fontsize=52)
    event = _event("This is a very long subtitle line that should overflow the half width for HSBS mode")

    fixed = apply_overflow_strategy(
        text=event.text,
        event=event,
        styles={"Default": style},
        resolution=Resolution(1920, 1080),
        mode=ConversionMode.HSBS,
        overflow_handling=OverflowHandling.SCALE_DOWN,
    )

    assert "\\fscx" in fixed
    match = re.search(r"\\fscx(\d+)", fixed)
    assert match is not None
    assert int(match.group(1)) < 50


def test_hsbs_scale_down_preserves_y_scale_after_transform_step() -> None:
    style = _style(fontsize=64)
    event = _event("This is a very long subtitle line that should overflow the half width for HSBS mode")

    fixed = apply_overflow_strategy(
        text=event.text,
        event=event,
        styles={"Default": style},
        resolution=Resolution(1920, 1080),
        mode=ConversionMode.HSBS,
        overflow_handling=OverflowHandling.SCALE_DOWN,
    )

    transformed = apply_position_and_transform_override(fixed, position=Position(100, 100), mode=ConversionMode.HSBS)

    x_match = re.search(r"\\fscx(\d+)", transformed)
    y_match = re.search(r"\\fscy(\d+)", transformed)
    assert x_match is not None
    assert y_match is not None
    assert int(y_match.group(1)) < 100


def test_newline_strategy_inserts_linebreaks() -> None:
    style = _style(fontsize=120)
    event = _event("This line starts here\\Nand continues here with many more words to overflow the half width")

    fixed = apply_overflow_strategy(
        text=event.text,
        event=event,
        styles={"Default": style},
        resolution=Resolution(1920, 1080),
        mode=ConversionMode.HSBS,
        overflow_handling=OverflowHandling.ADD_NEWLINES,
    )

    assert "\\N" in fixed
    assert "\\Nand continues" not in fixed


def test_scale_down_does_not_over_shrink_near_threshold() -> None:
    style = _style(fontsize=60)
    # Slight overflow in HSBS with current estimator.
    event = _event("This line is only a little too wide for the left right split today")

    fixed = apply_overflow_strategy(
        text=event.text,
        event=event,
        styles={"Default": style},
        resolution=Resolution(1920, 1080),
        mode=ConversionMode.HSBS,
        overflow_handling=OverflowHandling.SCALE_DOWN,
    )

    match = re.search(r"\\fscx(\d+)", fixed)
    assert match is not None
    assert int(match.group(1)) >= 45
