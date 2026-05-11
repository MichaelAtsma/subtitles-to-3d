from __future__ import annotations

import copy
import re
from dataclasses import dataclass

import pysubs2

from .models import ConversionMode, ConversionSettings, OverflowHandling, Resolution, SIZE_SCALE_FACTORS

POS_RE = re.compile(r"\\pos\(\s*-?\d+(?:\.\d+)?,\s*-?\d+(?:\.\d+)?\s*\)")
FSCX_RE = re.compile(r"\\fscx\s*-?\d+(?:\.\d+)?", re.IGNORECASE)
FSCY_RE = re.compile(r"\\fscy\s*-?\d+(?:\.\d+)?", re.IGNORECASE)
FSCX_VALUE_RE = re.compile(r"\\fscx\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)
FSCY_VALUE_RE = re.compile(r"\\fscy\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)
BRACE_RE = re.compile(r"\{[^}]*\}")

CHAR_WIDTH_FACTOR = 0.5
FIT_TARGET_RATIO = 0.98


@dataclass(frozen=True)
class Position:
    x: float
    y: float


SIDE_BY_SIDE_MODES = {ConversionMode.HSBS, ConversionMode.FSBS}


def convert_subtitles_to_mode(
    source_subs: pysubs2.SSAFile,
    resolution: Resolution,
    settings: ConversionSettings,
    mode: ConversionMode,
) -> pysubs2.SSAFile:
    output = copy.deepcopy(source_subs)
    output.events = []
    output.info["PlayResX"] = str(resolution.width)
    output.info["PlayResY"] = str(resolution.height)

    total_scale = _compute_total_font_scale(source_subs, resolution, settings)

    for style in output.styles.values():
        if style.fontsize and style.fontsize > 0:
            style.fontsize = int(round(style.fontsize * total_scale))

    for event in source_subs.events:
        if event.is_comment:
            continue

        fixed_text = apply_overflow_strategy(
            text=event.text,
            event=event,
            styles=output.styles,
            resolution=resolution,
            mode=mode,
            overflow_handling=settings.overflow_handling,
        )

        left_or_top, right_or_bottom = compute_pair_positions(
            event=event,
            styles=source_subs.styles,
            resolution=resolution,
            settings=settings,
            mode=mode,
        )

        first = copy.deepcopy(event)
        second = copy.deepcopy(event)
        first.text = fixed_text
        second.text = fixed_text

        first.text = apply_position_and_transform_override(first.text, left_or_top, mode)
        second.text = apply_position_and_transform_override(second.text, right_or_bottom, mode)

        output.events.append(first)
        output.events.append(second)

    return output


def compute_pair_positions(
    event: pysubs2.SSAEvent,
    styles: dict[str, pysubs2.SSAStyle],
    resolution: Resolution,
    settings: ConversionSettings,
    mode: ConversionMode,
) -> tuple[Position, Position]:
    style = styles.get(event.style) or styles.get("Default")
    if style is None:
        style = pysubs2.SSAStyle()

    base = _base_position(event, style, resolution)

    if mode == ConversionMode.HSBS or mode == ConversionMode.FSBS:
        left_x = base.x / 2 + settings.horizontal_offset
        right_x = (resolution.width / 2) + (base.x / 2) + settings.horizontal_offset
        y = base.y - settings.vertical_offset

        disparity = settings.pop_out
        left_x += disparity
        right_x -= disparity

        return clamp_position(Position(left_x, y), resolution), clamp_position(Position(right_x, y), resolution)

    if mode == ConversionMode.HOU:
        top_y = base.y / 2
        bottom_y = (resolution.height / 2) + (base.y / 2)
        x_top = base.x + settings.pop_out + (settings.horizontal_offset / 2)
        x_bottom = base.x - settings.pop_out - (settings.horizontal_offset / 2)

        top_y -= settings.vertical_offset
        bottom_y -= settings.vertical_offset

        return (
            clamp_position(Position(x_top, top_y), resolution),
            clamp_position(Position(x_bottom, bottom_y), resolution),
        )

    raise ValueError(f"Unsupported conversion mode: {mode}")


def _base_position(event: pysubs2.SSAEvent, style: pysubs2.SSAStyle, resolution: Resolution) -> Position:
    tagged_pos = _extract_position_from_text(event.text)
    if tagged_pos:
        return tagged_pos

    alignment = int(getattr(style, "alignment", 2) or 2)

    margin_l = event.marginl or style.marginl
    margin_r = event.marginr or style.marginr
    margin_v = event.marginv or style.marginv

    column = alignment % 3
    row = (alignment - 1) // 3

    if column == 1:
        x = margin_l
    elif column == 2:
        x = resolution.width / 2
    else:
        x = resolution.width - margin_r

    if row == 0:
        y = resolution.height - margin_v
    elif row == 1:
        y = resolution.height / 2
    else:
        y = margin_v

    return Position(float(x), float(y))


def _extract_position_from_text(text: str) -> Position | None:
    for block in BRACE_RE.findall(text):
        match = POS_RE.search(block)
        if not match:
            continue

        pos_text = match.group(0)[5:-1]
        x_str, y_str = pos_text.split(",", 1)
        return Position(float(x_str.strip()), float(y_str.strip()))

    return None


def apply_position_override(text: str, position: Position) -> str:
    rounded_x = int(round(position.x))
    rounded_y = int(round(position.y))

    if text.startswith("{") and "}" in text:
        first_close = text.find("}")
        block = text[1:first_close]
        cleaned = POS_RE.sub("", block)
        return "{" + cleaned + f"\\pos({rounded_x},{rounded_y})" + "}" + text[first_close + 1 :]

    stripped = remove_pos_tags(text)
    return "{\\pos(" + str(rounded_x) + "," + str(rounded_y) + ")}" + stripped


def apply_position_and_transform_override(text: str, position: Position, mode: ConversionMode) -> str:
    positioned = apply_position_override(text, position)

    if mode == ConversionMode.HSBS:
        return _apply_max_scale_overrides(positioned, max_scale_x=50, max_scale_y=None)
    if mode == ConversionMode.HOU:
        return _apply_max_scale_overrides(positioned, max_scale_x=None, max_scale_y=50)

    return positioned


def count_overflowing_events(
    source_subs: pysubs2.SSAFile,
    resolution: Resolution,
    mode: ConversionMode,
    settings: ConversionSettings,
) -> int:
    if mode not in SIDE_BY_SIDE_MODES:
        return 0

    overflow_count = 0
    total_scale = _compute_total_font_scale(source_subs, resolution, settings)

    for event in source_subs.events:
        if event.is_comment:
            continue
        style = source_subs.styles.get(event.style) or source_subs.styles.get("Default") or pysubs2.SSAStyle()
        effective_style = copy.deepcopy(style)
        if effective_style.fontsize and effective_style.fontsize > 0:
            effective_style.fontsize = int(round(effective_style.fontsize * total_scale))

        if is_text_overflowing_side(event.text, effective_style, event, resolution, mode):
            overflow_count += 1

    return overflow_count


def apply_overflow_strategy(
    text: str,
    event: pysubs2.SSAEvent,
    styles: dict[str, pysubs2.SSAStyle],
    resolution: Resolution,
    mode: ConversionMode,
    overflow_handling: OverflowHandling,
) -> str:
    if mode not in SIDE_BY_SIDE_MODES:
        return text
    if overflow_handling == OverflowHandling.NONE:
        return text

    style = styles.get(event.style) or styles.get("Default") or pysubs2.SSAStyle()
    if not is_text_overflowing_side(text, style, event, resolution, mode):
        return text

    if overflow_handling == OverflowHandling.SCALE_DOWN:
        return scale_text_x_to_fit(text, style, event, resolution, mode)

    if overflow_handling == OverflowHandling.ADD_NEWLINES:
        return wrap_text_to_fit(text, style, event, resolution, mode)

    return text


def is_text_overflowing_side(
    text: str,
    style: pysubs2.SSAStyle,
    event: pysubs2.SSAEvent,
    resolution: Resolution,
    mode: ConversionMode,
) -> bool:
    if mode not in SIDE_BY_SIDE_MODES:
        return False

    available = available_half_width(style, event, resolution)
    width = estimate_text_width(text, style.fontsize, mode)
    return width > available


def scale_text_x_to_fit(
    text: str,
    style: pysubs2.SSAStyle,
    event: pysubs2.SSAEvent,
    resolution: Resolution,
    mode: ConversionMode,
) -> str:
    available = max(1.0, available_half_width(style, event, resolution))
    current_width = max(1.0, estimate_text_width(text, style.fontsize, mode))
    ratio = min(1.0, (available * FIT_TARGET_RATIO) / current_width)

    base_scale_x = 50 if mode == ConversionMode.HSBS else 100
    adjusted_scale_x = max(5, int(round(base_scale_x * ratio)))
    adjusted_scale_x = min(base_scale_x, adjusted_scale_x)
    
    base_scale_y = 50 if mode == ConversionMode.HOU else 100
    adjusted_scale_y = round(base_scale_y * (adjusted_scale_x / base_scale_x))

    return _apply_scale_overrides(text, scale_x=adjusted_scale_x, scale_y=adjusted_scale_y)


def wrap_text_to_fit(
    text: str,
    style: pysubs2.SSAStyle,
    event: pysubs2.SSAEvent,
    resolution: Resolution,
    mode: ConversionMode,
) -> str:
    available = max(1.0, available_half_width(style, event, resolution))
    horizontal_scale = 50 if mode == ConversionMode.HSBS else 100
    unit_char_px = max(1.0, style.fontsize * CHAR_WIDTH_FACTOR * (horizontal_scale / 100.0))
    max_chars = max(5, int(available / unit_char_px))

    plain = extract_plain_text(text)
    reflowed = _reflow_plain_text(plain)
    wrapped = _wrap_plain_text(reflowed, max_chars)
    return replace_plain_text(text, wrapped)


def available_half_width(style: pysubs2.SSAStyle, event: pysubs2.SSAEvent, resolution: Resolution) -> float:
    margin_l = event.marginl or style.marginl
    margin_r = event.marginr or style.marginr
    half = resolution.width / 2.0
    return half - margin_l - margin_r


def estimate_text_width(text: str, fontsize: float, mode: ConversionMode) -> float:
    plain = extract_plain_text(text)
    longest = _longest_plain_line_length(plain)
    scale_x = 50 if mode == ConversionMode.HSBS else 100
    return longest * fontsize * CHAR_WIDTH_FACTOR * (scale_x / 100.0)


def extract_plain_text(text: str) -> str:
    cleaned = BRACE_RE.sub("", text)
    return cleaned.replace("\n", "\\N")


def replace_plain_text(text: str, new_plain: str) -> str:
    if text.startswith("{") and "}" in text:
        first_close = text.find("}")
        return text[: first_close + 1] + new_plain
    return new_plain


def _wrap_plain_text(text: str, max_chars: int) -> str:
    words = text.split()
    if not words:
        return ""

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)

    return "\\N".join(lines)


def _reflow_plain_text(text: str) -> str:
    return " ".join(part for part in text.replace("\\N", " ").split())


def _longest_plain_line_length(text: str) -> int:
    return max((len(line) for line in text.split("\\N")), default=0)


def _compute_total_font_scale(
    source_subs: pysubs2.SSAFile,
    resolution: Resolution,
    settings: ConversionSettings,
) -> float:
    # SRT files do not define PlayRes, so we assume legacy 384x288 for compensation.
    source_playres_x = float(source_subs.info.get("PlayResX", 384))
    source_playres_y = float(source_subs.info.get("PlayResY", 288))
    playres_scale_x = resolution.width / source_playres_x
    playres_scale_y = resolution.height / source_playres_y
    playres_compensation = (playres_scale_x + playres_scale_y) / 2.0
    user_scale = SIZE_SCALE_FACTORS[settings.subtitle_size]
    return playres_compensation * user_scale


def _apply_scale_overrides(text: str, scale_x: int | None, scale_y: int | None) -> str:
    if text.startswith("{") and "}" in text:
        first_close = text.find("}")
        block = text[1:first_close]
        cleaned = FSCX_RE.sub("", block)
        cleaned = FSCY_RE.sub("", cleaned)

        if scale_x is not None:
            cleaned += f"\\fscx{scale_x}"
        if scale_y is not None:
            cleaned += f"\\fscy{scale_y}"

        return "{" + cleaned + "}" + text[first_close + 1 :]

    prefix = "{"
    if scale_x is not None:
        prefix += f"\\fscx{scale_x}"
    if scale_y is not None:
        prefix += f"\\fscy{scale_y}"
    prefix += "}"
    return prefix + text


def _apply_max_scale_overrides(text: str, max_scale_x: int | None, max_scale_y: int | None) -> str:
    current_x = _extract_scale_value(text, FSCX_VALUE_RE)
    current_y = _extract_scale_value(text, FSCY_VALUE_RE)

    next_x: int | None = None
    next_y: int | None = None

    if max_scale_x is not None:
        if current_x is None:
            next_x = max_scale_x
        else:
            next_x = int(min(max_scale_x, round(current_x)))

    if max_scale_y is not None:
        if current_y is None:
            next_y = max_scale_y
        else:
            next_y = int(min(max_scale_y, round(current_y)))

    # Preserve existing values on axes not constrained by this call.
    if max_scale_x is None and current_x is not None:
        next_x = int(round(current_x))
    if max_scale_y is None and current_y is not None:
        next_y = int(round(current_y))

    return _apply_scale_overrides(text, scale_x=next_x, scale_y=next_y)


def _extract_scale_value(text: str, pattern: re.Pattern[str]) -> float | None:
    if not (text.startswith("{") and "}" in text):
        return None

    first_close = text.find("}")
    block = text[1:first_close]
    match = pattern.search(block)
    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def remove_pos_tags(text: str) -> str:
    def _clean_block(match: re.Match[str]) -> str:
        block = match.group(0)
        cleaned = POS_RE.sub("", block)
        return cleaned

    return BRACE_RE.sub(_clean_block, text)


def clamp_position(position: Position, resolution: Resolution) -> Position:
    return Position(
        x=max(0, min(position.x, float(resolution.width))),
        y=max(0, min(position.y, float(resolution.height))),
    )
