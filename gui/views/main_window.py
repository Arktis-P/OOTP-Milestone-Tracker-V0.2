"""
Main Window App Shell & Sidebar Navigation (Phase 5.1)
Implements Windows 11 modern sidebar navigation shell for all 10 views.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QStatusBar
)
from PySide6.QtCore import Qt
from gui.theme.theme import apply_dark_theme
from gui.views.dashboard_view import DashboardView
from gui.views.achievement_records_view import AchievementRecordsView
from gui.views.player_stats_view import PlayerStatsView
from gui.views.prediction_view import PredictionView
from gui.views.streak_view import StreakView
from gui.views.record_import_center_view import RecordImportCenterView
from gui.views.manual_records_view import ManualRecordsView
from gui.views.rating_editor_view import RatingEditorView
from gui.views.settings_view import SettingsView
from gui.views.advanced_tools_view import AdvancedToolsView


class MainWindow(QMainWindow):
    def __init__(self, settings_mgr=None):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.setWindowTitle("OOTP Milestone Tracker V0.2")
        self.resize(1150, 720)

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Navigation List
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(230)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #141417;
                border-right: 1px solid #2a2a30;
                padding-top: 15px;
            }
            QListWidget::item {
                height: 38px;
                padding-left: 15px;
                color: #b0b0bb;
                font-weight: 600;
                border-radius: 4px;
                margin: 2px 8px;
            }
            QListWidget::item:hover {
                background-color: #242429;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #0066cc;
                color: #ffffff;
            }
        """)

        # Add Menu Items
        self.menu_map = [
            ("📊 Dashboard", "Dashboard"),
            ("🏆 Achievement Records", "Achievement Records"),
            ("⚾ Player Stats", "Player Stats"),
            ("🔮 Milestone Predictions", "Predictions"),
            ("🔥 Streak Records", "Streak Records"),
            ("📥 Record Import Center", "Record Import Center"),
            ("✍️ Manual Records", "Manual Records"),
            ("✏️ Rating Editor", "Rating Editor"),
            ("⚙️ Settings", "Settings"),
            ("🛠️ Advanced Tools", "Advanced Tools"),
        ]

        for label, _ in self.menu_map:
            item = QListWidgetItem(label)
            self.sidebar.addItem(item)

        main_layout.addWidget(self.sidebar)

        # 2. Main Stacked Widget
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)

        # Build Page Instances
        self.pages = {}

        dashboard_page = DashboardView(self.settings_mgr, navigate_callback=self.navigate_to_page)
        records_page = AchievementRecordsView(self.settings_mgr)
        player_stats_page = PlayerStatsView(self.settings_mgr)
        prediction_page = PredictionView(self.settings_mgr)
        streak_page = StreakView(self.settings_mgr)
        import_center_page = RecordImportCenterView(self.settings_mgr)
        manual_page = ManualRecordsView(self.settings_mgr)
        rating_editor_page = RatingEditorView(self.settings_mgr)
        settings_page = SettingsView(self.settings_mgr, on_settings_changed=self._on_settings_changed)
        advanced_tools_page = AdvancedToolsView(self.settings_mgr)

        self.pages["Dashboard"] = (0, dashboard_page)
        self.pages["Achievement Records"] = (1, records_page)
        self.pages["Player Stats"] = (2, player_stats_page)
        self.pages["Predictions"] = (3, prediction_page)
        self.pages["Streak Records"] = (4, streak_page)
        self.pages["Record Import Center"] = (5, import_center_page)
        self.pages["Manual Records"] = (6, manual_page)
        self.pages["Rating Editor"] = (7, rating_editor_page)
        self.pages["Settings"] = (8, settings_page)
        self.pages["Advanced Tools"] = (9, advanced_tools_page)

        for _, (_, widget) in sorted(self.pages.items(), key=lambda item: item[1][0]):
            self.stacked_widget.addWidget(widget)

        self.sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        self.setCentralWidget(central_widget)

        self.statusBar().showMessage("OOTP Milestone Tracker V0.2 ready")
        self.sidebar.setCurrentRow(0)

    def _on_sidebar_changed(self, row: int):
        self.stacked_widget.setCurrentIndex(row)
        # Auto refresh views on tab switch
        current_widget = self.stacked_widget.currentWidget()
        if isinstance(current_widget, DashboardView):
            current_widget.refresh_dashboard()
        elif isinstance(current_widget, AchievementRecordsView):
            current_widget.load_records()
        elif isinstance(current_widget, PlayerStatsView):
            current_widget.load_stats()

    def navigate_to_page(self, page_key: str):
        if page_key in self.pages:
            idx, _ = self.pages[page_key]
            self.sidebar.setCurrentRow(idx)

    def _on_settings_changed(self, settings):
        dashboard_idx, dashboard_widget = self.pages["Dashboard"]
        if isinstance(dashboard_widget, DashboardView):
            dashboard_widget.settings = settings
            dashboard_widget.refresh_dashboard()
