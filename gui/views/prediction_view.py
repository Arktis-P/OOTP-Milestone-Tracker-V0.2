"""
Milestone Predictions View (Phase 6.2)
Displays projected pace, near-target highlights, and remaining stat goals.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar
)
from PySide6.QtCore import Qt
from core.config.settings import SettingsManager
from core.db.connection import DatabaseManager
from core.prediction.model import PredictionEngine


class PredictionView(QWidget):
    def __init__(self, settings_mgr: SettingsManager):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.settings = self.settings_mgr.load()
        self.paths = self.settings_mgr.get_derived_paths(self.settings)

        self._init_ui()
        self.load_predictions()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Milestone Predictions (마일스톤 달성 예측)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["선수명", "목표 마일스톤", "현재값", "목표값", "남은 수치", "시즌 페이스", "예상 최종", "계산 근거"])
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_predictions(self):
        db_mgr = DatabaseManager(self.paths.db_path)
        db_mgr.initialize_database()
        with db_mgr.get_connection() as conn:
            engine = PredictionEngine(conn)
            results = engine.generate_predictions(season=self.settings.current_season)

            self.table.setRowCount(len(results))
            for i, r in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(r.player_name))
                self.table.setItem(i, 1, QTableWidgetItem(r.label))
                self.table.setItem(i, 2, QTableWidgetItem(f"{r.current_value:.0f}"))
                self.table.setItem(i, 3, QTableWidgetItem(f"{r.target:.0f}"))

                rem_item = QTableWidgetItem(f"{r.remaining:.0f}")
                if r.is_near:
                    rem_item.setForeground(Qt.GlobalColor.yellow)
                self.table.setItem(i, 4, rem_item)

                self.table.setItem(i, 5, QTableWidgetItem(f"{r.season_pace:.3f} / 경기"))
                self.table.setItem(i, 6, QTableWidgetItem(f"{r.projected_final:.1f}"))
                self.table.setItem(i, 7, QTableWidgetItem(r.explanation))
