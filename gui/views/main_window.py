"""
Main Application Window View (PySide6)
"""

try:
    from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QStatusBar
    from PySide6.QtCore import Qt

    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False


if PYSIDE_AVAILABLE:
    class MainWindow(QMainWindow):
        def __init__(self, settings_mgr=None):
            super().__init__()
            self.settings_mgr = settings_mgr
            self.setWindowTitle("OOTP Milestone Tracker V0.2")
            self.resize(1100, 700)

            central_widget = QWidget()
            layout = QVBoxLayout(central_widget)

            label = QLabel("OOTP Milestone Tracker V0.2 MVP")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333333;")

            sublabel = QLabel("App Shell & Core Scaffolding Initialized")
            sublabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

            layout.addWidget(label)
            layout.addWidget(sublabel)

            self.setCentralWidget(central_widget)
            self.statusBar().showMessage("Ready")
else:
    class MainWindow:
        def __init__(self, settings_mgr=None):
            raise ImportError("PySide6 package is required for MainWindow.")
