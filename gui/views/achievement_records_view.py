"""
Achievement Records View (Phase 5.4)
Displays recorded milestone events with grade badges, filters, and 1-click Export & Share.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from core.config.settings import SettingsManager
from core.db.connection import DatabaseManager


GRADE_COLOR_MAP = {
    "common": "#a0a0a0",
    "uncommon": "#00e676",
    "rare": "#00b0ff",
    "epic": "#aa00ff",
    "legendary": "#ffab00",
}


class AchievementRecordsView(QWidget):
    def __init__(self, settings_mgr: SettingsManager):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.settings = self.settings_mgr.load()
        self.paths = self.settings_mgr.get_derived_paths(self.settings)

        self._init_ui()
        self.load_records()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_layout = QHBoxLayout()
        title = QLabel("Achievement Records (마일스톤 달성 기록)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        self.export_btn = QPushButton("📋 마일스톤 요약 복사 (공유)")
        self.export_btn.clicked.connect(self._export_summary)
        title_layout.addWidget(self.export_btn)

        layout.addLayout(title_layout)

        # Filters Group
        filter_group = QGroupBox("기록 필터 및 검색")
        filter_layout = QHBoxLayout(filter_group)

        filter_layout.addWidget(QLabel("등급:"))
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["전체 (All)", "legendary", "epic", "rare", "uncommon", "common"])
        self.grade_combo.currentIndexChanged.connect(self.load_records)
        filter_layout.addWidget(self.grade_combo)

        filter_layout.addWidget(QLabel("구분:"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["전체 (All)", "batting", "pitching", "team"])
        self.cat_combo.currentIndexChanged.connect(self.load_records)
        filter_layout.addWidget(self.cat_combo)

        filter_layout.addWidget(QLabel("검색어:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("선수명 또는 마일스톤 키워드...")
        self.search_input.textChanged.connect(self.load_records)
        filter_layout.addWidget(self.search_input, 1)

        layout.addWidget(filter_group)

        # Records Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["날짜", "시즌", "선수/대상", "마일스톤 기록", "등급", "달성값", "기준값"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_records(self):
        db_path = self.paths.db_path
        db_mgr = DatabaseManager(db_path)
        db_mgr.initialize_database()
        with db_mgr.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT m.event_date, m.season, COALESCE(p.display_name, '팀 기록') as subject_name,
                       m.policy_key, m.category, m.grade, m.value, m.threshold
                FROM milestone_events m
                LEFT JOIN players p ON m.player_id = p.id
                WHERE 1=1
            """
            params = []

            selected_grade = self.grade_combo.currentText()
            if selected_grade != "전체 (All)":
                query += " AND m.grade = ?"
                params.append(selected_grade)

            selected_cat = self.cat_combo.currentText()
            if selected_cat != "전체 (All)":
                query += " AND m.category = ?"
                params.append(selected_cat)

            search_kw = self.search_input.text().strip()
            if search_kw:
                query += " AND (p.display_name LIKE ? OR m.policy_key LIKE ?)"
                params.extend([f"%{search_kw}%", f"%{search_kw}%"])

            query += " ORDER BY m.event_date DESC, m.id DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            self.table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(r["event_date"])))
                self.table.setItem(i, 1, QTableWidgetItem(str(r["season"])))
                self.table.setItem(i, 2, QTableWidgetItem(str(r["subject_name"])))
                self.table.setItem(i, 3, QTableWidgetItem(str(r["policy_key"])))

                grade_item = QTableWidgetItem(str(r["grade"]).upper())
                color_hex = GRADE_COLOR_MAP.get(r["grade"].lower(), "#ffffff")
                grade_item.setForeground(Qt.GlobalColor.white)
                self.table.setItem(i, 4, grade_item)

                self.table.setItem(i, 5, QTableWidgetItem(str(r["value"])))
                self.table.setItem(i, 6, QTableWidgetItem(str(r["threshold"])))

    def _export_summary(self):
        text_lines = ["🏆 [OOTP Milestone Tracker 달성 기록 요약]"]
        for i in range(min(15, self.table.rowCount())):
            date = self.table.item(i, 0).text()
            name = self.table.item(i, 2).text()
            policy = self.table.item(i, 3).text()
            grade = self.table.item(i, 4).text()
            text_lines.append(f"• [{date}] {name} - {policy} ({grade})")

        summary_text = "\n".join(text_lines)
        QApplication.clipboard().setText(summary_text)
        QMessageBox.information(self, "복사 완료", "클립보드에 마일스톤 달성 요약이 복사되었습니다!")
