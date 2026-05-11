from __future__ import annotations

from pathlib import Path

import cv2

from .models import ConversionSettings, Resolution, ResolutionMode

STANDARD_RESOLUTIONS: dict[str, Resolution] = {
    "480p": Resolution(854, 480),
    "720p": Resolution(1280, 720),
    "1080p": Resolution(1920, 1080),
    "1440p": Resolution(2560, 1440),
    "4K UHD": Resolution(3840, 2160),
    "8K UHD": Resolution(7680, 4320),
}


class ResolutionError(RuntimeError):
    pass


def resolve_resolution(settings: ConversionSettings) -> Resolution:
    if settings.resolution_mode == ResolutionMode.STANDARD:
        res = STANDARD_RESOLUTIONS.get(settings.standard_preset_key)
        if not res:
            raise ResolutionError(f"Unknown standard resolution preset: {settings.standard_preset_key}")
        return res

    if settings.resolution_mode == ResolutionMode.CUSTOM:
        if settings.custom_width <= 0 or settings.custom_height <= 0:
            raise ResolutionError("Custom resolution must use positive width and height.")
        return Resolution(settings.custom_width, settings.custom_height)

    if settings.resolution_mode == ResolutionMode.FROM_VIDEO:
        if not settings.video_file:
            raise ResolutionError("Video file must be selected when using 'From video file'.")
        return get_video_resolution(settings.video_file)

    raise ResolutionError(f"Unsupported resolution mode: {settings.resolution_mode}")


def get_video_resolution(video_path: Path) -> Resolution:
    if not video_path.exists():
        raise ResolutionError(f"Video file does not exist: {video_path}")

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ResolutionError(f"Unable to open video file: {video_path}")

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    capture.release()

    if width <= 0 or height <= 0:
        raise ResolutionError(f"Unable to determine resolution from video file: {video_path}")

    return Resolution(width, height)
