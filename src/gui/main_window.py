from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QSizePolicy,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from src.core.batch import convert_files
from src.core.converter import SIDE_BY_SIDE_MODES, count_overflowing_events
from src.core.models import ConversionMode, ConversionSettings, OverflowHandling, ResolutionMode, SubtitleSize
from src.core.parser import SUPPORTED_EXTENSIONS
from src.core.parser import load_subtitles
from src.core.resolution import STANDARD_RESOLUTIONS
from src.core.resolution import resolve_resolution


class SubtitleDropList(QListWidget):
    filesDropped = pyqtSignal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths: list[Path] = []
        for url in event.mimeData().urls():
            local = Path(url.toLocalFile())
            if local.suffix.lower() in SUPPORTED_EXTENSIONS and local.is_file():
                paths.append(local)

        if paths:
            self.filesDropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()


class InfoToolButton(QToolButton):
    hover_delay_ms = 200
    tooltip_duration_ms = 8000

    def __init__(self, tooltip_text: str) -> None:
        super().__init__()
        self.setObjectName("InfoButton")
        self.setText("?")
        self.setAutoRaise(True)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setToolTip(tooltip_text)
        self.setToolTipDuration(self.tooltip_duration_ms)
        self.setFixedSize(20, 20)

        if self.hover_delay_ms:
            self._tooltip_timer = QTimer(self)
            self._tooltip_timer.setSingleShot(True)
            self._tooltip_timer.setInterval(self.hover_delay_ms)
            self._tooltip_timer.timeout.connect(self._show_tooltip_now)

    def enterEvent(self, event) -> None:  # type: ignore[override]
        if self.hover_delay_ms:
            self._tooltip_timer.start()
        else:
            self._show_tooltip_now()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        if self.hover_delay_ms:
            self._tooltip_timer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    def _show_tooltip_now(self) -> None:
        if not self.underMouse():
            return
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), self.toolTip(), self, self.rect(), self.tooltip_duration_ms)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Subtitle to 3D .ass Converter")
        self.resize(1100, 760)

        self.file_paths: list[Path] = []

        self._build_ui()
        self._wire_events()
        self._update_resolution_controls()
        self._update_override_controls()

    def _build_ui(self) -> None:
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        title = QLabel("Subtitle to 3D .ass")
        title.setObjectName("HeaderLabel")
        subtitle = QLabel("Convert SRT / ASS / VTT into HSBS / FSBS / HOU .ass subtitles")
        subtitle.setObjectName("SubHeaderLabel")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        main_grid = QGridLayout()
        main_grid.setHorizontalSpacing(12)
        main_grid.setVerticalSpacing(12)
        main_grid.setColumnStretch(0, 0)#1)
        main_grid.setColumnStretch(1, 0)#1)
        main_grid.setRowStretch(0, 1)
        main_grid.setRowStretch(1, 0)
        main_grid.setRowStretch(2, 0)

        main_grid.addWidget(self._build_files_group(), 0, 0)
        main_grid.addWidget(self._build_conversion_group(), 0, 1, 2, 1)
        main_grid.addWidget(self._build_output_group(), 1, 0)
        main_grid.addWidget(self._build_log_group(), 2, 0)
        main_grid.addWidget(self._build_error_group(), 2, 1)

        outer.addLayout(main_grid)

        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setObjectName("ConvertButton")
        outer.addWidget(self.convert_btn)

        self.setCentralWidget(root)

    def _make_info_button(self, message: str) -> QToolButton:
        return InfoToolButton(message)

    def _label_with_info(self, label_text: str, info_text: str) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(2, 0, 2, 0)
        row.setSpacing(6)
        label = QLabel(label_text)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(label)
        row.addWidget(self._make_info_button(info_text))
        row.addStretch(1)
        return container

    def _build_files_group(self) -> QGroupBox:
        group = QGroupBox("Subtitle Files")
        layout = QVBoxLayout(group)

        helper = QLabel("Drag and drop subtitle files here, or use Add Files.")
        layout.addWidget(helper)

        self.file_list = SubtitleDropList()
        self.file_list.setMinimumHeight(160)
        layout.addWidget(self.file_list)

        row = QHBoxLayout()
        self.add_files_btn = QPushButton("Add Files")
        self.remove_selected_btn = QPushButton("Remove Selected")
        self.clear_files_btn = QPushButton("Clear")
        row.addWidget(self.add_files_btn)
        row.addWidget(self.remove_selected_btn)
        row.addWidget(self.clear_files_btn)
        layout.addLayout(row)

        return group

    def _build_conversion_group(self) -> QGroupBox:
        group = QGroupBox("Conversion")
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(group)

        mode_row = QHBoxLayout()
        mode_row.addWidget(
            self._label_with_info(
                "Mode",
                "HSBS creates a half side-by-side output, FSBS creates a full side-by-side output, HOU creates a half over-under output, and ALL generates all three.",
            )
        )
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            [
                ConversionMode.HSBS.value,
                ConversionMode.FSBS.value,
                ConversionMode.HOU.value,
                ConversionMode.ALL.value,
            ]
        )
        self.mode_combo.setCurrentText(ConversionMode.ALL.value)
        self.mode_combo.setMinimumWidth(0)
        self.mode_combo.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        mode_row.addWidget(self.mode_combo)
        layout.addLayout(mode_row)

        resolution_box = QGroupBox("Resolution")
        r_layout = QGridLayout(resolution_box)

        self.standard_radio = QRadioButton("Standard size")
        self.custom_radio = QRadioButton("Custom")
        self.video_radio = QRadioButton("From video file")

        self.resolution_group = QButtonGroup(self)
        self.resolution_group.addButton(self.standard_radio)
        self.resolution_group.addButton(self.custom_radio)
        self.resolution_group.addButton(self.video_radio)
        self.standard_radio.setChecked(True)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(STANDARD_RESOLUTIONS.keys()))
        self.preset_combo.setCurrentText("1080p")
        self.preset_combo.setMinimumWidth(0)
        self.preset_combo.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)

        self.custom_width_spin = QSpinBox()
        self.custom_width_spin.setRange(64, 20000)
        self.custom_width_spin.setValue(1920)
        self.custom_width_spin.setMinimumWidth(0)

        self.custom_height_spin = QSpinBox()
        self.custom_height_spin.setRange(64, 20000)
        self.custom_height_spin.setValue(1080)
        self.custom_height_spin.setMinimumWidth(0)
        self.custom_height_spin.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)

        self.video_file_edit = QLineEdit()
        self.video_file_edit.setPlaceholderText("No video selected")
        self.video_file_edit.setMinimumWidth(0)
        self.video_file_edit.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.video_browse_btn = QPushButton("Choose file")
        self.video_browse_btn.setMinimumWidth(0)
        self.video_browse_btn.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.video_radio.setStyleSheet("padding-right: 16px;")

        r_layout.setHorizontalSpacing(10)
        r_layout.setColumnStretch(0, 0)
        r_layout.setColumnStretch(1, 0)#1)
        r_layout.setColumnStretch(2, 0)#1)
        r_layout.setColumnStretch(3, 0)#1)
        r_layout.setColumnStretch(4, 0)#0)

        r_layout.addWidget(self.standard_radio, 0, 0)
        r_layout.addWidget(self.preset_combo, 0, 1, 1, 2)

        r_layout.addWidget(self.custom_radio, 1, 0)
        r_layout.addWidget(QLabel("Width:"), 1, 1)
        r_layout.addWidget(self.custom_width_spin, 1, 2)
        r_layout.addWidget(QLabel("Height:"), 1, 3)
        r_layout.addWidget(self.custom_height_spin, 1, 4)

        r_layout.addWidget(self.video_radio, 2, 0)
        r_layout.addWidget(self.video_file_edit, 2, 1, 1, 3)
        r_layout.addWidget(self.video_browse_btn, 2, 4)

        layout.addWidget(resolution_box)

        depth_box = QGroupBox("Subtitle positioning")
        d_layout = QGridLayout(depth_box)
        d_layout.setColumnStretch(0, 0)#1)
        d_layout.setColumnStretch(1, 0)

        self.horizontal_offset_spin = QSpinBox()
        self.horizontal_offset_spin.setRange(-500, 500)
        self.horizontal_offset_spin.setValue(0)
        self.horizontal_offset_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)

        self.vertical_offset_spin = QSpinBox()
        self.vertical_offset_spin.setRange(-500, 500)
        self.vertical_offset_spin.setValue(0)
        self.vertical_offset_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)

        self.pop_out_spin = QSpinBox()
        self.pop_out_spin.setRange(-500, 500)
        self.pop_out_spin.setValue(0)
        self.pop_out_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)

        d_layout.addWidget(
            self._label_with_info(
                "Horizontal offset",
                "Moves both subtitle copies together horizontally. Positive values move both to the right; negative values move both to the left.",
            ),
            0,
            0,
        )
        d_layout.addWidget(self.horizontal_offset_spin, 0, 1)
        d_layout.addWidget(
            self._label_with_info(
                "Vertical offset",
                "Moves the subtitle up or down. Positive numbers move it up; negative numbers move it down.",
            ),
            1,
            0,
        )
        d_layout.addWidget(self.vertical_offset_spin, 1, 1)
        d_layout.addWidget(
            self._label_with_info(
                "Pop-out",
                "Adds extra 3D separation. Keep this between -15 and 15 if you want your brain to merge the two texts reliably.",
            ),
            2,
            0,
        )
        d_layout.addWidget(self.pop_out_spin, 2, 1)

        layout.addWidget(depth_box)

        size_box = QGroupBox("Subtitle Size")
        s_layout = QGridLayout(size_box)

        s_layout.addWidget(
            self._label_with_info(
                "Font size",
                "Controls the final rendered font size after conversion. Medium is the default, with larger or smaller options available for manual adjustment.",
            ),
            0,
            0,
        )
        self.size_combo = QComboBox()
        self.size_combo.addItems([
            "Very Small",
            "Small",
            "Medium",
            "Large",
            "Very Large",
        ])
        self.size_combo.setCurrentText("Medium")
        self.size_combo.setMinimumWidth(0)
        self.size_combo.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        s_layout.addWidget(self.size_combo, 0, 1)
        s_layout.setColumnStretch(0, 0)#1)
        s_layout.setColumnStretch(1, 0)#1)

        layout.addWidget(size_box)

        return group

    def _build_output_group(self) -> QGroupBox:
        group = QGroupBox("Output")
        layout = QVBoxLayout(group)

        self.override_name_check = QCheckBox("Override output base name")
        self.override_name_edit = QLineEdit()
        self.override_name_edit.setPlaceholderText("Example: movie_subs")

        note = QLabel("Auto output names are input.<MODE>.ass (HSBS / FSBS / HOU).")
        layout.addWidget(self.override_name_check)
        layout.addWidget(self.override_name_edit)
        layout.addWidget(note)

        return group

    def _build_log_group(self) -> QGroupBox:
        group = QGroupBox("Progress")
        layout = QVBoxLayout(group)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(40)
        layout.addWidget(self.log_text)
        return group

    def _build_error_group(self) -> QGroupBox:
        group = QGroupBox("Validation & Errors")
        layout = QVBoxLayout(group)
        self.error_list = QListWidget()
        self.error_list.setMinimumHeight(40)
        layout.addWidget(self.error_list)
        return group

    def _wire_events(self) -> None:
        self.add_files_btn.clicked.connect(self._add_files_from_dialog)
        self.remove_selected_btn.clicked.connect(self._remove_selected)
        self.clear_files_btn.clicked.connect(self._clear_files)
        self.file_list.filesDropped.connect(self._append_files)

        self.standard_radio.toggled.connect(self._update_resolution_controls)
        self.custom_radio.toggled.connect(self._update_resolution_controls)
        self.video_radio.toggled.connect(self._update_resolution_controls)
        self.preset_combo.currentIndexChanged.connect(self._activate_standard_resolution)
        self.custom_width_spin.valueChanged.connect(self._activate_custom_resolution)
        self.custom_height_spin.valueChanged.connect(self._activate_custom_resolution)
        self.video_file_edit.textEdited.connect(self._activate_video_resolution)
        self.video_browse_btn.clicked.connect(self._choose_video_file)

        self.override_name_check.toggled.connect(self._update_override_controls)
        self.convert_btn.clicked.connect(self._start_conversion)

    def _append_files(self, paths: list[Path]) -> None:
        new_paths = 0
        for path in paths:
            if path not in self.file_paths:
                self.file_paths.append(path)
                self.file_list.addItem(str(path))
                new_paths += 1

        if new_paths:
            self._log(f"Added {new_paths} file(s).")

    def _add_files_from_dialog(self) -> None:
        pattern = "Subtitle files (*.srt *.ass *.vtt)"
        files, _ = QFileDialog.getOpenFileNames(self, "Choose subtitle files", "", pattern)
        self._append_files([Path(item) for item in files])

    def _remove_selected(self) -> None:
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return

        selected_paths = {Path(item.text()) for item in selected_items}
        self.file_paths = [p for p in self.file_paths if p not in selected_paths]

        for item in selected_items:
            row = self.file_list.row(item)
            self.file_list.takeItem(row)

        self._log(f"Removed {len(selected_items)} file(s).")

    def _clear_files(self) -> None:
        count = len(self.file_paths)
        self.file_paths.clear()
        self.file_list.clear()
        if count:
            self._log("Cleared selected files.")

    def _choose_video_file(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Choose video file",
            "",
            "Video files (*.mp4 *.mkv *.avi *.mov *.wmv *.webm)",
        )
        if file_name:
            self.video_file_edit.setText(file_name)
            self.video_radio.setChecked(True)

    def _update_resolution_controls(self) -> None:
        self.preset_combo.setEnabled(True)
        self.custom_width_spin.setEnabled(True)
        self.custom_height_spin.setEnabled(True)
        self.video_file_edit.setEnabled(True)
        self.video_browse_btn.setEnabled(True)

    def _activate_standard_resolution(self) -> None:
        self.standard_radio.setChecked(True)

    def _activate_custom_resolution(self) -> None:
        self.custom_radio.setChecked(True)

    def _activate_video_resolution(self, text: str) -> None:
        if text.strip():
            self.video_radio.setChecked(True)

    def _update_override_controls(self) -> None:
        self.override_name_edit.setEnabled(self.override_name_check.isChecked())

    def _start_conversion(self) -> None:
        self.error_list.clear()
        self.log_text.clear()

        if not self.file_paths:
            self._show_error("Select at least one subtitle file before converting.")
            return

        settings = self._collect_settings()
        if settings is None:
            return

        settings = self._resolve_overflow_strategy(settings)
        if settings is None:
            return

        self.convert_btn.setEnabled(False)
        try:
            results, errors = convert_files(self.file_paths, settings, progress=self._log)
        finally:
            self.convert_btn.setEnabled(True)

        total_outputs = 0
        for result in results:
            for output in result.outputs:
                total_outputs += 1
                self._log(f"{result.source_file.name} -> {output.output_file.name}")

        for error in errors:
            self.error_list.addItem(QListWidgetItem(error))

        if errors:
            self._show_warning(f"Converted with {len(errors)} error(s). See Validation & Errors panel.")
        else:
            self._show_info(f"Done. Wrote {total_outputs} output file(s).")

    def _collect_settings(self) -> ConversionSettings | None:
        mode = ConversionMode(self.mode_combo.currentText())

        if self.standard_radio.isChecked():
            resolution_mode = ResolutionMode.STANDARD
            video_file = None
        elif self.custom_radio.isChecked():
            resolution_mode = ResolutionMode.CUSTOM
            video_file = None
        else:
            resolution_mode = ResolutionMode.FROM_VIDEO
            raw_video = self.video_file_edit.text().strip()
            if not raw_video:
                self._show_error("Choose a video file when 'From video file' is selected.")
                return None
            video_file = Path(raw_video)

        override_base = self.override_name_edit.text().strip() if self.override_name_check.isChecked() else None

        size_text = self.size_combo.currentText()
        size_map = {
            "Very Small": SubtitleSize.VERY_SMALL,
            "Small": SubtitleSize.SMALL,
            "Medium": SubtitleSize.MEDIUM,
            "Large": SubtitleSize.LARGE,
            "Very Large": SubtitleSize.VERY_LARGE,
        }
        subtitle_size = size_map.get(size_text, SubtitleSize.MEDIUM)

        settings = ConversionSettings(
            conversion_mode=mode,
            resolution_mode=resolution_mode,
            standard_preset_key=self.preset_combo.currentText(),
            custom_width=self.custom_width_spin.value(),
            custom_height=self.custom_height_spin.value(),
            video_file=video_file,
            horizontal_offset=self.horizontal_offset_spin.value(),
            vertical_offset=self.vertical_offset_spin.value(),
            pop_out=self.pop_out_spin.value(),
            output_override_base=override_base,
            subtitle_size=subtitle_size,
        )

        if abs(settings.pop_out) > 15:
            QMessageBox.warning(
                self,
                "Pop-Out Warning",
                "Pop-out values outside -15 to 15 may be too strong for the viewer to merge cleanly. The conversion will continue anyway.",
            )

        return settings

    def _resolve_overflow_strategy(self, settings: ConversionSettings) -> ConversionSettings | None:
        modes = self._target_modes(settings.conversion_mode)
        side_by_side_modes = [mode for mode in modes if mode in SIDE_BY_SIDE_MODES]
        if not side_by_side_modes:
            return settings

        try:
            resolution = resolve_resolution(settings)
        except Exception as exc:
            self._show_error(str(exc))
            return None

        total_overflow = 0
        for subtitle_file in self.file_paths:
            try:
                subs = load_subtitles(subtitle_file)
            except Exception as exc:
                self._show_error(f"Failed to validate {subtitle_file.name}: {exc}")
                return None

            for mode in side_by_side_modes:
                total_overflow += count_overflowing_events(subs, resolution, mode, settings)

        if total_overflow == 0:
            return settings

        choice = self._ask_overflow_fix_choice(total_overflow)
        if choice is None:
            return None

        return replace(settings, overflow_handling=choice)

    def _target_modes(self, conversion_mode: ConversionMode) -> list[ConversionMode]:
        if conversion_mode == ConversionMode.ALL:
            return [mode for mode in ConversionMode if mode != ConversionMode.ALL]
        return [conversion_mode]

    def _ask_overflow_fix_choice(self, overflow_count: int) -> OverflowHandling | None:
        box = QMessageBox(self)
        box.setWindowTitle("Possible Side-By-Side Overflow")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText(
            f"Detected {overflow_count} subtitle line(s) that may cross between left/right halves. "
            "Choose how to fix problematic lines."
        )

        scale_btn = box.addButton("Scale down to fit", QMessageBox.ButtonRole.AcceptRole)
        newline_btn = box.addButton("Add extra newlines", QMessageBox.ButtonRole.AcceptRole)
        continue_btn = box.addButton("Continue without fix", QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked == scale_btn:
            return OverflowHandling.SCALE_DOWN
        if clicked == newline_btn:
            return OverflowHandling.ADD_NEWLINES
        if clicked == continue_btn:
            return OverflowHandling.NONE
        if clicked == cancel_btn:
            return None

        return None

    def _log(self, message: str) -> None:
        self.log_text.appendPlainText(message)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)

    def _show_warning(self, message: str) -> None:
        QMessageBox.warning(self, "Finished with Warnings", message)

    def _show_info(self, message: str) -> None:
        QMessageBox.information(self, "Success", message)
