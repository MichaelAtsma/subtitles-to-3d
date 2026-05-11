from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class ConversionMode(str, Enum):
    HSBS = "HSBS"
    FSBS = "FSBS"
    HOU = "HOU"
    ALL = "ALL"


class ResolutionMode(str, Enum):
    STANDARD = "standard"
    CUSTOM = "custom"
    FROM_VIDEO = "from_video"


class SubtitleSize(str, Enum):
    VERY_SMALL = "very_small"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    VERY_LARGE = "very_large"


class OverflowHandling(str, Enum):
    NONE = "none"
    SCALE_DOWN = "scale_down"
    ADD_NEWLINES = "add_newlines"


# Font size scale factors relative to original
# PlayRes compensation is applied automatically based on source/target resolution
SIZE_SCALE_FACTORS = {
    SubtitleSize.VERY_SMALL: 0.5,
    SubtitleSize.SMALL: 0.75,
    SubtitleSize.MEDIUM: 1.0,
    SubtitleSize.LARGE: 1.5,
    SubtitleSize.VERY_LARGE: 2.0,
}


@dataclass(frozen=True)
class Resolution:
    width: int
    height: int


@dataclass(frozen=True)
class ConversionSettings:
    conversion_mode: ConversionMode
    resolution_mode: ResolutionMode
    standard_preset_key: str = "1080p"
    custom_width: int = 1920
    custom_height: int = 1080
    video_file: Optional[Path] = None
    horizontal_offset: int = 0
    vertical_offset: int = 0
    pop_out: int = 0
    output_override_base: Optional[str] = None
    subtitle_size: SubtitleSize = SubtitleSize.MEDIUM
    overflow_handling: OverflowHandling = OverflowHandling.NONE


@dataclass(frozen=True)
class ConvertRequest:
    subtitle_file: Path
    settings: ConversionSettings


@dataclass(frozen=True)
class ConvertedOutput:
    mode: ConversionMode
    output_file: Path


@dataclass(frozen=True)
class ConvertResult:
    source_file: Path
    outputs: list[ConvertedOutput]
    warnings: list[str]


@dataclass(frozen=True)
class ConversionError:
    source_file: Path
    message: str
