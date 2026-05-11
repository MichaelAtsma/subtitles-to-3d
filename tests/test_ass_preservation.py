from __future__ import annotations

from pathlib import Path

from src.core.converter import convert_subtitles_to_mode
from src.core.models import ConversionMode, ConversionSettings, Resolution, ResolutionMode
from src.core.parser import load_subtitles


def test_ass_style_name_is_preserved(tmp_path: Path) -> None:
    ass_file = tmp_path / "styled.ass"
    ass_file.write_text(
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1920\n"
        "PlayResY: 1080\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Fancy,Arial,42,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,0,2,20,20,60,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:00.00,0:00:01.00,Fancy,,0,0,0,,Styled line\n",
        encoding="utf-8",
    )

    source = load_subtitles(ass_file)
    settings = ConversionSettings(
        conversion_mode=ConversionMode.HSBS,
        resolution_mode=ResolutionMode.STANDARD,
    )

    converted = convert_subtitles_to_mode(source, Resolution(1920, 1080), settings, ConversionMode.HSBS)

    assert "Fancy" in converted.styles
    assert len(converted.events) == 2
    assert converted.events[0].style == "Fancy"
    assert converted.events[1].style == "Fancy"
