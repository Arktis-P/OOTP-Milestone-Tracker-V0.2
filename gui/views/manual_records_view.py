"""
Manual Records View (Phase 8.1 & 8.2)
Provides forms to register manual milestone events and temporary players.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QMessageBox
)
from core.config.settings import SettingsManager
from core.db.connection import DatabaseManager
from core.db.manual_event_repo import ManualEventRepository


class ManualRecordsView(QWidget):
    def __init__(self, settings_mgr: SettingsManager):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.settings = self.settings_mgr.load()
        self.paths = self.settings_mgr.get_derived_paths(self.settings)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Manual Records (수동 기록 입력 및 선수 등록)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        form_group = QGroupBox("수동 이벤트 등록 폼")
        form_layout = QVBoxLayout(form_group)

        # Event type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("이벤트 유형:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["award (수상)", "trade (이적/트레이드)", "injury (부상)", "hof (명예의 전당)", "postseason (포스트시즌)", "custom (기타)"])
        type_layout.addWidget(self.type_combo, 1)
        form_layout.addLayout(type_layout)

        # Player Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("선수 이름:"))
        self.fname_input = QLineEdit()
        self.fname_input.setPlaceholderText("이름 (First Name e.g. Shohei)")
        self.lname_input = QLineEdit()
        self.lname_input.setPlaceholderText("성 (Last Name e.g. Ohtani)")
        name_layout.addWidget(self.fname_input)
        name_layout.addWidget(self.lname_input)
        form_layout.addLayout(name_layout)

        # Date & Season
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("날짜 (YYYY-MM-DD):"))
        self.date_input = QLineEdit()
        self.date_input.setText(f"{self.settings.current_season}-07-01")
        date_layout.addWidget(self.date_input)

        date_layout.addWidget(QLabel("시즌:"))
        self.season_input = QLineEdit()
        self.season_input.setText(str(self.settings.current_season))
        date_layout.addWidget(self.season_input)
        form_layout.addLayout(date_layout)

        # Title & Description
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("제목/기록명:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("예: 2026 AL MVP 수상")
        title_layout.addWidget(self.title_input, 1)
        form_layout.addLayout(title_layout)

        form_layout.addWidget(QLabel("상세 설명:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        form_layout.addWidget(self.desc_input)

        # Submit button
        submit_btn = QPushButton("수동 기록 저장")
        submit_btn.setObjectName("accentButton")
        submit_btn.clicked.connect(self._save_manual_event)
        form_layout.addWidget(submit_btn)

        layout.addWidget(form_group)
        layout.addStretch()

    def _save_manual_event(self):
        fname = self.fname_input.text().strip()
        lname = self.lname_input.text().strip()
        evt_title = self.title_input.text().strip()
        evt_date = self.date_input.text().strip()
        evt_type_raw = self.type_combo.currentText().split(" ")[0]

        if not fname or not evt_title:
            QMessageBox.warning(self, "경고", "선수 이름과 기록 제목은 필수 항목입니다.")
            return

        try:
            season = int(self.season_input.text().strip())
        except ValueError:
            season = self.settings.current_season

        try:
            db_mgr = DatabaseManager(self.paths.db_path)
            db_mgr.initialize_database()
            with db_mgr.get_connection() as conn:
                repo = ManualEventRepository(conn)
                res = repo.add_manual_event(
                    event_type=evt_type_raw,
                    first_name=fname,
                    last_name=lname,
                    season=season,
                    event_date=evt_date,
                    title=evt_title,
                    description=self.desc_input.toPlainText().strip()
                )
                QMessageBox.information(self, "성공", f"[{res['display_name']}] 수동 기록이 성공적으로 저장되었습니다.")
                self.title_input.clear()
                self.desc_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"수동 기록 저장 실패:\n{e}")
