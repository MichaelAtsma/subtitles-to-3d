from __future__ import annotations


def app_stylesheet() -> str:
    return """
    QWidget {
        background-color: #f7f8fb;
        color: #152238;
        font-family: "Poppins", "Segoe UI", sans-serif;
        font-size: 12px;
    }

    QMainWindow {
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #f7f8fb, stop: 0.5 #eef5ff, stop: 1 #fff2e8);
    }

    QGroupBox {
        border: 1px solid #cad6e8;
        border-radius: 12px;
        margin-top: 12px;
        padding: 10px;
        background-color: rgba(255, 255, 255, 0.85);
        font-weight: 600;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: #20426a;
    }

    QPushButton {
        border-radius: 10px;
        border: 1px solid #94b5db;
        background-color: #d9ebff;
        padding: 6px 10px;
        color: #10345e;
        font-weight: 600;
    }

    QPushButton:hover {
        background-color: #c7e0ff;
    }

    QPushButton:pressed {
        background-color: #b7d6ff;
    }

    QPushButton#ConvertButton {
        background-color: #1f6fd2;
        color: #ffffff;
        border-color: #1a60b6;
        padding: 8px 12px;
        font-size: 13px;
    }

    QPushButton#ConvertButton:hover {
        background-color: #1b63bc;
    }

    QListWidget, QPlainTextEdit, QLineEdit, QComboBox, QSpinBox {
        border: 1px solid #bfd0e4;
        border-radius: 8px;
        padding: 4px;
        background-color: #ffffff;
    }

    QComboBox {
        min-width: 0px;
        padding-right: 22px;
    }

    QSpinBox {
        padding-right: 0px;
    }

    QSpinBox::up-button, QSpinBox::down-button {
        subcontrol-origin: padding;
        width: 18px;
    }

    QSpinBox::up-button {
        subcontrol-position: top right;
    }

    QSpinBox::down-button {
        subcontrol-position: bottom right;
    }

    QToolButton#InfoButton {
        border: 1px solid #94b5db;
        border-radius: 9px;
        background-color: #f3f8ff;
        color: #1f6fd2;
        font-weight: 700;
        min-width: 16px;
        max-width: 16px;
        min-height: 16px;
        max-height: 16px;
        padding: 0px;
    }

    QToolButton#InfoButton:hover {
        background-color: #dcecff;
    }

    QRadioButton, QCheckBox {
        color: #1d2e45;
        spacing: 6px;
        height: 24px;
        padding: 0px 10px 0px 4px;
    }

    QRadioButton::indicator {
        width: 10px;
        height: 10px;
        border-radius: 7px;
    }

    QRadioButton::indicator:unchecked {
        background-color: #ffffff;
        border: 2px solid #94b5db;
    }

    QRadioButton::indicator:checked {
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #1f6fd2, stop: 1 #1a60b6);
        border: 2px solid #1a60b6;
    }

    QCheckBox::indicator {
        width: 10px;
        height: 10px;
    }

    QCheckBox::indicator:unchecked {
        background-color: #ffffff;
        border: 2px solid #94b5db;
    }

    QCheckBox::indicator:checked {
        background-color: #1f6fd2;
        border: 2px solid #1a60b6;
    }

    QLabel {
        color: #1d2e45;
        padding: 0px 10px 0px 10px;
    }

    QLabel#HeaderLabel {
        font-size: 20px;
        font-weight: 700;
        color: #0f2f56;
    }

    QLabel#SubHeaderLabel {
        color: #355680;
        font-size: 12px;
    }
    """
