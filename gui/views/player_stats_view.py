"""
Player Stats View (Phase 5.5)
Displays Batting and Pitching stats for season and career baselines.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget
)
from core.config.settings import SettingsManager
from core.db.connection import DatabaseManager


class PlayerStatsView(QWidget):
    def __init__(self, settings_mgr: SettingsManager):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.settings = self.settings_mgr.load()
        self.paths = self.settings_mgr.get_derived_paths(self.settings)

        self._init_ui()
        self.load_stats()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Player Stats (선수 시즌 및 통산 기록)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("시즌 선택:"))
        self.season_combo = QComboBox()
        self.season_combo.addItems([str(self.settings.current_season), "2025", "2024"])
        self.season_combo.currentIndexChanged.connect(self.load_stats)
        filter_layout.addWidget(self.season_combo)

        filter_layout.addWidget(QLabel("선수 검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("선수 이름 검색...")
        self.search_input.textChanged.connect(self.load_stats)
        filter_layout.addWidget(self.search_input, 1)

        layout.addLayout(filter_layout)

        # Tabs for Batting & Pitching
        self.tabs = QTabWidget()

        # Batting Tab
        self.bat_table = QTableWidget()
        self.bat_table.setColumnCount(12)
        self.bat_table.setHorizontalHeaderLabels(["선수명", "팀", "G", "AB", "R", "H", "HR", "RBI", "SB", "AVG", "OBP", "OPS"])
        self.bat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.bat_table, "타자 기록 (Batting)")

        # Pitching Tab
        self.pitch_table = QTableWidget()
        self.pitch_table.setColumnCount(12)
        self.pitch_table.setHorizontalHeaderLabels(["선수명", "팀", "G", "GS", "W", "L", "SV", "IP(Outs)", "SO", "HR", "ERA", "WHIP"])
        self.pitch_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.pitch_table, "투수 기록 (Pitching)")

        layout.addWidget(self.tabs)

    def load_stats(self):
        db_mgr = DatabaseManager(self.paths.db_path)
        db_mgr.initialize_database()
        with db_mgr.get_connection() as conn:
            cursor = conn.cursor()
            season = int(self.season_combo.currentText()) if self.season_combo.currentText().isdigit() else 2026
            search_kw = self.search_input.text().strip()

            # Load Batting
            b_query = """
                SELECT p.display_name, b.team_id, b.g, b.ab, b.r, b.h, b.hr, b.rbi, b.sb, b.avg, b.obp, b.ops
                FROM baseline_batting_stats b
                JOIN players p ON b.player_id = p.id
                WHERE b.season = ?
            """
            params = [season]
            if search_kw:
                b_query += " AND p.display_name LIKE ?"
                params.append(f"%{search_kw}%")
            b_query += " ORDER BY b.h DESC LIMIT 200"

            cursor.execute(b_query, params)
            b_rows = cursor.fetchall()
            self.bat_table.setRowCount(len(b_rows))
            for i, r in enumerate(b_rows):
                self.bat_table.setItem(i, 0, QTableWidgetItem(str(r["display_name"])))
                self.bat_table.setItem(i, 1, QTableWidgetItem(str(r["team_id"])))
                self.bat_table.setItem(i, 2, QTableWidgetItem(str(r["g"])))
                self.bat_table.setItem(i, 3, QTableWidgetItem(str(r["ab"])))
                self.bat_table.setItem(i, 4, QTableWidgetItem(str(r["r"])))
                self.bat_table.setItem(i, 5, QTableWidgetItem(str(r["h"])))
                self.bat_table.setItem(i, 6, QTableWidgetItem(str(r["hr"])))
                self.bat_table.setItem(i, 7, QTableWidgetItem(str(r["rbi"])))
                self.bat_table.setItem(i, 8, QTableWidgetItem(str(r["sb"])))
                self.bat_table.setItem(i, 9, QTableWidgetItem(f"{r['avg']:.3f}"))
                self.bat_table.setItem(i, 10, QTableWidgetItem(f"{r['obp']:.3f}"))
                self.bat_table.setItem(i, 11, QTableWidgetItem(f"{r['ops']:.3f}"))

            # Load Pitching
            p_query = """
                SELECT p.display_name, b.team_id, b.g, b.gs, b.w, b.l, b.sv, b.ip_outs, b.k, b.hr, b.era, b.whip
                FROM baseline_pitching_stats b
                JOIN players p ON b.player_id = p.id
                WHERE b.season = ?
            """
            params_p = [season]
            if search_kw:
                p_query += " AND p.display_name LIKE ?"
                params_p.append(f"%{search_kw}%")
            p_query += " ORDER BY b.w DESC, b.k DESC LIMIT 200"

            cursor.execute(p_query, params_p)
            p_rows = cursor.fetchall()
            self.pitch_table.setRowCount(len(p_rows))
            for i, r in enumerate(p_rows):
                self.pitch_table.setItem(i, 0, QTableWidgetItem(str(r["display_name"])))
                self.pitch_table.setItem(i, 1, QTableWidgetItem(str(r["team_id"])))
                self.pitch_table.setItem(i, 2, QTableWidgetItem(str(r["g"])))
                self.pitch_table.setItem(i, 3, QTableWidgetItem(str(r["gs"])))
                self.pitch_table.setItem(i, 4, QTableWidgetItem(str(r["w"])))
                self.pitch_table.setItem(i, 5, QTableWidgetItem(str(r["l"])))
                self.pitch_table.setItem(i, 6, QTableWidgetItem(str(r["sv"])))
                self.pitch_table.setItem(i, 7, QTableWidgetItem(str(r["ip_outs"])))
                self.pitch_table.setItem(i, 8, QTableWidgetItem(str(r["k"])))
                self.pitch_table.setItem(i, 9, QTableWidgetItem(str(r["hr"])))
                self.pitch_table.setItem(i, 10, QTableWidgetItem(f"{r['era']:.2f}"))
                self.pitch_table.setItem(i, 11, QTableWidgetItem(f"{r['whip']:.2f}"))
