from PySide6.QtGui import QFont

DARK_QSS = """
QWidget { background: #111318; color: #e7eaf0; font-size: 12px; }
QMainWindow { background: #111318; }
#sidebar { background: #0c0e12; border-right: 1px solid #252a33; }
#topbar { background: #111318; border-bottom: 1px solid #252a33; }
#pageTitle { font-size: 16px; font-weight: 700; }
#muted { color: #8f98a8; }
#sectionTitle { font-size: 13px; font-weight: 700; color: #f3f5f8; }
#statBox { background: #171a21; border: 1px solid #292f39; border-radius: 6px; }
#statValue { font-size: 20px; font-weight: 700; }
QPushButton { background: transparent; border: 0; border-radius: 5px; padding: 7px 9px; text-align: left; }
QPushButton:hover { background: #1b1f27; }
QPushButton:checked { background: #202938; color: #79a8ff; }
QPushButton#primary { background: #3275d8; color: white; text-align: center; }
QPushButton#primary:hover { background: #3d82e6; }
QLineEdit, QComboBox { background: #171a21; border: 1px solid #303641; border-radius: 5px; padding: 6px 8px; min-height: 20px; }
QLineEdit:focus, QComboBox:focus { border-color: #4d8fe8; }
QTableWidget { background: #111318; alternate-background-color: #14171d; border: 1px solid #292f39; border-radius: 5px; gridline-color: #222831; selection-background-color: #203653; }
QHeaderView::section { background: #171a21; color: #aeb6c3; border: 0; border-bottom: 1px solid #303641; padding: 6px 8px; font-weight: 600; }
QTableCornerButton::section { background: #171a21; border: 0; }
QProgressBar { background: #22262e; border: 0; border-radius: 3px; height: 6px; text-align: center; color: transparent; }
QProgressBar::chunk { background: #4d8fe8; border-radius: 3px; }
QTabWidget::pane { border: 0; }
QTabBar::tab { background: transparent; color: #8f98a8; padding: 7px 10px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #e7eaf0; border-bottom-color: #4d8fe8; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #343a45; border-radius: 4px; min-height: 24px; }
QToolTip { background: #20242c; color: #eef1f5; border: 1px solid #343a45; padding: 4px; }
"""

LIGHT_QSS = """
QWidget { background: #f5f6f8; color: #20242a; font-size: 12px; }
#sidebar { background: #eef0f3; border-right: 1px solid #d8dce2; }
#topbar { background: #f5f6f8; border-bottom: 1px solid #d8dce2; }
#pageTitle { font-size: 16px; font-weight: 700; }
#muted { color: #697281; }
#sectionTitle { font-size: 13px; font-weight: 700; }
#statBox { background: white; border: 1px solid #d9dde4; border-radius: 6px; }
#statValue { font-size: 20px; font-weight: 700; }
QPushButton { background: transparent; border: 0; border-radius: 5px; padding: 7px 9px; text-align: left; }
QPushButton:hover { background: #e4e8ee; }
QPushButton:checked { background: #dce8f8; color: #215da8; }
QPushButton#primary { background: #3275d8; color: white; text-align: center; }
QLineEdit, QComboBox { background: white; border: 1px solid #ccd2da; border-radius: 5px; padding: 6px 8px; min-height: 20px; }
QTableWidget { background: white; alternate-background-color: #f8f9fb; border: 1px solid #d9dde4; border-radius: 5px; gridline-color: #e8ebef; selection-background-color: #dce8f8; }
QHeaderView::section { background: #f0f2f5; color: #5f6876; border: 0; border-bottom: 1px solid #d9dde4; padding: 6px 8px; font-weight: 600; }
QProgressBar { background: #e2e6eb; border: 0; border-radius: 3px; height: 6px; color: transparent; }
QProgressBar::chunk { background: #3275d8; border-radius: 3px; }
QTabWidget::pane { border: 0; }
QTabBar::tab { color: #697281; padding: 7px 10px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #20242a; border-bottom-color: #3275d8; }
"""


def apply_theme(app, theme: str) -> None:
    app.setStyleSheet(LIGHT_QSS if theme == "light" else DARK_QSS)
    font = QFont("Segoe UI", 9)
    app.setFont(font)
