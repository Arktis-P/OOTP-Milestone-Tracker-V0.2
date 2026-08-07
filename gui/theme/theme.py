"""
UI Theme & QSS Stylesheet Manager (Phase 5)
Provides modern Windows 11 dark theme and styled widget helpers.
"""

DARK_THEME_QSS = """
QMainWindow {
    background-color: #1a1a1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Pretendard', sans-serif;
}

QWidget {
    background-color: #1a1a1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Pretendard', sans-serif;
}

QListWidget, QTableWidget, QTreeWidget, QTextEdit {
    background-color: #242429;
    border: 1px solid #33333d;
    border-radius: 6px;
    color: #f0f0f0;
    gridline-color: #33333d;
}

QHeaderView::section {
    background-color: #2a2a30;
    color: #b0b0bb;
    padding: 6px;
    border: none;
    font-weight: bold;
}

QPushButton {
    background-color: #2b2d38;
    color: #ffffff;
    border: 1px solid #3d4050;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #383a48;
    border-color: #505468;
}

QPushButton:pressed {
    background-color: #1e2028;
}

QPushButton#accentButton {
    background-color: #0066cc;
    border: 1px solid #0077ee;
}

QPushButton#accentButton:hover {
    background-color: #0077ee;
}

QComboBox, QLineEdit, QSpinBox {
    background-color: #242429;
    border: 1px solid #3d4050;
    border-radius: 6px;
    padding: 6px;
    color: #ffffff;
}

QGroupBox {
    border: 1px solid #33333d;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: bold;
    color: #00aaff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QStatusBar {
    background-color: #141417;
    color: #888899;
}
"""


def apply_dark_theme(app):
    app.setStyleSheet(DARK_THEME_QSS)
