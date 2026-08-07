"""
Dashboard View (Phase 5.6)
Displays summary cards (active save, readiness, last import, milestone count) and recent achievements.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from core.config.settings import SettingsManager
from core.db.connection import DatabaseManager


class DashboardView(QWidget):
    def __init__(self, settings_mgr: SettingsManager, navigate_callback=None):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.navigate_callback = navigate_callback
        self.settings = self.settings_mgr.load()

        self._init_ui()
        self.refresh_dashboard()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("OOTP Milestone Tracker Dashboard")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Stat Cards Grid
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.save_card = self._create_card("활성 세이브", "Not Configured", "#00aaff")
        self.readiness_card = self._create_card("데이터 준비 상태", "미완료", "#ff5252")
        self.milestone_count_card = self._create_card("총 마일스톤 달성", "0 건", "#00e676")

        cards_layout.addWidget(self.save_card)
        cards_layout.addWidget(self.readiness_card)
        cards_layout.addWidget(self.milestone_count_card)

        layout.addLayout(cards_layout)

        # Quick Actions
        actions_group = QGroupBox("빠른 작업 (Quick Actions)")
        actions_layout = QHBoxLayout(actions_group)

        btn_import = QPushButton("📥 Record Import Center 이동")
        btn_import.setObjectName("accentButton")
        btn_import.clicked.connect(lambda: self.navigate_callback("Record Import Center") if self.navigate_callback else None)

        btn_records = QPushButton("🏆 Achievement Records 보기")
        btn_records.clicked.connect(lambda: self.navigate_callback("Achievement Records") if self.navigate_callback else None)

        btn_settings = QPushButton("⚙️ 설정 변경")
        btn_settings.clicked.connect(lambda: self.navigate_callback("Settings") if self.navigate_callback else None)

        actions_layout.addWidget(btn_import)
        actions_layout.addWidget(btn_records)
        actions_layout.addWidget(btn_settings)

        layout.addWidget(actions_group)

        # Recent Milestones List
        recent_group = QGroupBox("최근 달성된 마일스톤")
        recent_layout = QVBoxLayout(recent_group)

        self.recent_list = QListWidget()
        recent_layout.addWidget(self.recent_list)

        layout.addWidget(recent_group)

    def _create_card(self, title_text: str, value_text: str, color_hex: str) -> QGroupBox:
        box = QGroupBox()
        b_layout = QVBoxLayout(box)

        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet("color: #a0a0b0; font-size: 12px; font-weight: bold;")

        lbl_val = QLabel(value_text)
        lbl_val.setStyleSheet(f"color: {color_hex}; font-size: 16px; font-weight: bold;")
        lbl_val.setWordWrap(True)

        b_layout.addWidget(lbl_title)
        b_layout.addWidget(lbl_val)
        return box

    def refresh_dashboard(self):
        readiness = self.settings_mgr.check_readiness(self.settings)

        # Update Save Card
        save_name = readiness["save_key"]
        if self.settings.active_save_path:
            save_name = os.path.basename(self.settings.active_save_path)
        self.save_card.findChildren(QLabel)[1].setText(save_name)

        # Update Readiness Card
        if readiness["is_ready"]:
            self.readiness_card.findChildren(QLabel)[1].setText("🟢 준비 완료 (Ready)")
            self.readiness_card.findChildren(QLabel)[1].setStyleSheet("color: #00e676; font-size: 15px; font-weight: bold;")
        else:
            self.readiness_card.findChildren(QLabel)[1].setText("🔴 세이브 미지정")
            self.readiness_card.findChildren(QLabel)[1].setStyleSheet("color: #ff5252; font-size: 15px; font-weight: bold;")

        # Fetch Milestone Count & Recent Items
        paths = self.settings_mgr.get_derived_paths(self.settings)
        db_mgr = DatabaseManager(paths.db_path)
        db_mgr.initialize_database()
        with db_mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM milestone_events")
            m_count = cursor.fetchone()[0]
            self.milestone_count_card.findChildren(QLabel)[1].setText(f"{m_count} 건")

            cursor.execute(
                """SELECT m.event_date, COALESCE(p.display_name, '팀') as name, m.policy_key, m.grade
                   FROM milestone_events m LEFT JOIN players p ON m.player_id = p.id
                   ORDER BY m.event_date DESC, m.id DESC LIMIT 10"""
            )
            rows = cursor.fetchall()
            self.recent_list.clear()
            if not rows:
                self.recent_list.addItem("아직 달성된 마일스톤이 없습니다. Import Center에서 박스스코어를 가져와 보세요!")
            else:
                for r in rows:
                    item_str = f"[{r['event_date']}] {r['name']} - {r['policy_key']} ({r['grade'].upper()})"
                    self.recent_list.addItem(QListWidgetItem(item_str))
