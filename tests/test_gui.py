"""
Unit tests for GUI Views & Application Shell (Phase 5)
"""

import sys
import pytest
from PySide6.QtWidgets import QApplication
from core.config.settings import SettingsManager, Settings
from gui.theme.theme import apply_dark_theme
from gui.views.main_window import MainWindow
from gui.views.settings_view import SettingsView
from gui.views.record_import_center_view import RecordImportCenterView
from gui.views.achievement_records_view import AchievementRecordsView
from gui.views.player_stats_view import PlayerStatsView
from gui.views.dashboard_view import DashboardView


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_gui_views_initialization(qapp, tmp_path):
    config_dir = str(tmp_path / "app_config")
    mgr = SettingsManager(config_dir=config_dir)

    apply_dark_theme(qapp)

    window = MainWindow(settings_mgr=mgr)
    assert window.windowTitle() == "OOTP Milestone Tracker V0.2"
    assert window.stacked_widget.count() == 10

    # Test page navigation across all 10 pages
    for key in ["Dashboard", "Achievement Records", "Player Stats", "Predictions", "Streak Records",
                "Record Import Center", "Manual Records", "Rating Editor", "Settings", "Advanced Tools"]:
        window.navigate_to_page(key)
        idx, _ = window.pages[key]
        assert window.stacked_widget.currentIndex() == idx
