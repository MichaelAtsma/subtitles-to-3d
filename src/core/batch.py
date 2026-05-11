from __future__ import annotations

from pathlib import Path
from typing import Callable

from .ass_writer import write_ass
from .converter import convert_subtitles_to_mode
from .models import ConversionMode, ConversionSettings, ConvertedOutput, ConvertResult
from .parser import load_subtitles
from .resolution import resolve_resolution

ProgressCallback = Callable[[str], None]


def convert_files(
    subtitle_files: list[Path],
    settings: ConversionSettings,
    progress: ProgressCallback | None = None,
) -> tuple[list[ConvertResult], list[str]]:
    results: list[ConvertResult] = []
    errors: list[str] = []

    for subtitle_file in subtitle_files:
        try:
            if progress:
                progress(f"Loading {subtitle_file.name}...")

            subs = load_subtitles(subtitle_file)
            resolution = resolve_resolution(settings)
            modes = _get_modes(settings.conversion_mode)

            outputs: list[ConvertedOutput] = []
            warnings: list[str] = []

            for mode in modes:
                converted = convert_subtitles_to_mode(
                    source_subs=subs,
                    resolution=resolution,
                    settings=settings,
                    mode=mode,
                )

                output_file = build_output_path(
                    source_subtitle=subtitle_file,
                    mode=mode,
                    override_base_name=settings.output_override_base,
                )
                output_file = avoid_collision(output_file)
                write_ass(converted, output_file)
                outputs.append(ConvertedOutput(mode=mode, output_file=output_file))

                if progress:
                    progress(f"Wrote {output_file.name}")

            results.append(ConvertResult(source_file=subtitle_file, outputs=outputs, warnings=warnings))

        except Exception as exc:
            errors.append(f"{subtitle_file.name}: {exc}")
            if progress:
                progress(f"Failed for {subtitle_file.name}: {exc}")

    return results, errors


def _get_modes(conversion_mode: ConversionMode) -> list[ConversionMode]:
    if conversion_mode == ConversionMode.ALL:
        return [mode for mode in ConversionMode if mode != ConversionMode.ALL]
    return [conversion_mode]


def build_output_path(source_subtitle: Path, mode: ConversionMode, override_base_name: str | None = None) -> Path:
    base = override_base_name.strip() if override_base_name else source_subtitle.stem
    return source_subtitle.with_name(f"{base}.{mode.value}.ass")


def avoid_collision(path: Path) -> Path:
    if not path.exists():
        return path

    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
