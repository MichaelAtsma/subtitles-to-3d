from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen

from src.gui.main_window import MainWindow
from src.gui.theme import app_stylesheet


def _base_path() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def _asset_path(*parts: str) -> Path:
    return _base_path().joinpath("src", "gui", "assets", *parts)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(app_stylesheet())

    icon_path = _asset_path("app_icon.png")
    app_icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    splash: QSplashScreen | None = None
    splash_path = _asset_path("splash.png")
    if splash_path.exists():
        splash_pixmap = QPixmap(str(splash_path))
        if not splash_pixmap.isNull():
            splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
            splash.show()
            app.processEvents()

    window = MainWindow()
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)

    if splash is not None:
        def _show_main_window() -> None:
            window.show()
            splash.finish(window)

        QTimer.singleShot(900, _show_main_window)
    else:
        window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
