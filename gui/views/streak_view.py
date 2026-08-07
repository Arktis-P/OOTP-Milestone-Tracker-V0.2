"""
Streak Records View (Phase 7.3)
Displays active hitting/win streaks and historical ended streak records.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget
)
from core.config.settings import SettingsManager
from core.db.connection import DatabaseManager


class StreakView(QWidget):
    def __init__(self, settings_mgr: SettingsManager):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.settings = self.settings_mgr.load()
        self.paths = self.settings_mgr.get_derived_paths(self.settings)

        self._init_ui()
        self.load_streaks()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Streak Center (연속 기록 센터)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        self.tabs = QTabWidget()

        # Active Streaks Tab
        self.active_table = QTableWidget()
        self.active_table.setColumnCount(6)
        self.active_table.setHorizontalHeaderLabels(["대상", "기록 종류", "현재 연속 기록", "시작일", "최근 경기일", "시즌"])
        self.active_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.active_table, "진행 중인 기록 (Active Streaks)")

        # Ended Streaks History Tab
        self.ended_table = QTableWidget()
        self.ended_table.setColumnCount(6)
        self.ended_table.setHorizontalHeaderLabels(["대상", "기록 종류", "최종 달성 기록", "시작일", "종료일", "시즌"])
        self.ended_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.ended_table, "종료된 통산 기록 (Ended Streaks)")

        layout.addWidget(self.tabs)

    def load_streaks(self):
        db_mgr = DatabaseManager(self.paths.db_path)
        db_mgr.initialize_database()
        with db_mgr.get_connection() as conn:
            cursor = conn.cursor()

            # Active Streaks
            cursor.execute(
                """SELECT s.policy_key, s.subject_type, s.current_value, s.start_date, s.last_date, s.season,
                          COALESCE(p.display_name, '팀') as subject_name
                   FROM streak_states s LEFT JOIN players p ON (s.subject_type = 'player' AND s.subject_id = p.id)
                   WHERE s.season = ? ORDER BY s.current_value DESC""",
                (self.settings.current_season,)
            )
            active_rows = cursor.fetchall()
            self.active_table.setRowCount(len(active_rows))
            for i, r in enumerate(active_rows):
                self.active_table.setItem(i, 0, QTableWidgetItem(r["subject_name"]))
                self.active_table.setItem(i, 1, QTableWidgetItem(r["policy_key"]))
                self.active_table.setItem(i, 2, QTableWidgetItem(f"{r['current_value']} 경기"))
                self.active_table.setItem(i, 3, QTableWidgetItem(r["start_date"]))
                self.active_table.setItem(i, 4, QTableWidgetItem(r["last_date"]))
                self.active_table.setItem(i, 5, QTableWidgetItem(str(r["season"])))

            # Ended Streaks
            cursor.execute(
                """SELECT s.policy_key, s.subject_type, s.final_value, s.start_date, s.end_date, s.season,
                          COALESCE(p.display_name, '팀') as subject_name
                   FROM streak_events s LEFT JOIN players p ON (s.subject_type = 'player' AND s.subject_id = p.id)
                   WHERE s.season = ? ORDER BY s.final_value DESC""",
                (self.settings.current_season,)
            )
            ended_rows = cursor.fetchall()
            self.ended_table.setRowCount(len(ended_rows))
            for i, r in enumerate(ended_rows):
                self.ended_table.setItem(i, 0, QTableWidgetItem(r["subject_name"]))
                self.ended_table.setItem(i, 1, QTableWidgetItem(r["policy_key"]))
                self.ended_table.setItem(i, 2, QTableWidgetItem(f"{r['final_value']} 경기"))
                self.ended_table.setItem(i, 3, QTableWidgetItem(r["start_date"]))
                self.ended_table.setItem(i, 4, QTableWidgetItem(r["end_date"]))
                self.ended_table.setItem(i, 5, QTableWidgetItem(str(r["season"])))
