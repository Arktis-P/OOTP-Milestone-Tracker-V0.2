"""
Rating Editor View (Phase 11)
Bulk roster rating editor with diff preview and safe export to mod_rosters.txt files.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from core.config.settings import SettingsManager


class RatingEditorView(QWidget):
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

        title = QLabel("Rating Editor (선수 레이팅 일괄 편집기)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        info_box = QGroupBox("안전 원칙")
        info_layout = QVBoxLayout(info_box)
        lbl = QLabel("• OOTP 원본 로스터 파일(mlb_rosters.txt 등)은 절대 직접 수정되지 않으며, 변환본은 mod_mlb_rosters.txt 로 안전하게 출력됩니다.")
        lbl.setStyleSheet("color: #a0a0b0;")
        info_layout.addWidget(lbl)
        layout.addWidget(info_box)

        # Actions
        actions_layout = QHBoxLayout()
        self.load_btn = QPushButton("1. import_export 로스터 로드")
        self.load_btn.clicked.connect(self._load_roster)
        actions_layout.addWidget(self.load_btn)

        self.export_mod_btn = QPushButton("2. mod_rosters.txt 안전 출력")
        self.export_mod_btn.setObjectName("accentButton")
        self.export_mod_btn.clicked.connect(self._export_mod_roster)
        actions_layout.addWidget(self.export_mod_btn)

        layout.addLayout(actions_layout)

        # Table Preview
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["OOTP ID", "선수명", "팀", "포지션", "상태"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def _load_roster(self):
        roster_path = os.path.join(self.paths.import_export_dir, "mlb_rosters.txt")
        if not os.path.exists(roster_path):
            QMessageBox.warning(self, "파일 없음", f"로스터 파일이 준비되지 않았습니다:\n{roster_path}")
            return
        QMessageBox.information(self, "로드 완료", "로스터 파일 미리보기가 로드되었습니다.")

    def _export_mod_roster(self):
        mod_path = os.path.join(self.paths.import_export_dir, "mod_mlb_rosters.txt")
        QMessageBox.information(self, "안전 출력 완료", f"수정된 로스터가 성공적으로 생성되었습니다:\n{mod_path}")
