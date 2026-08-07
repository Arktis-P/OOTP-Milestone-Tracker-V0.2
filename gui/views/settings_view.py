"""
Settings View (Phase 5.2)
Allows selecting OOTP save directory, active save, current season, tracked teams, and displays readiness.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from core.config.settings import SettingsManager, Settings


class SettingsView(QWidget):
    def __init__(self, settings_mgr: SettingsManager, on_settings_changed=None):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.on_settings_changed = on_settings_changed
        self.settings = self.settings_mgr.load()

        self._init_ui()
        self._load_values()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("앱 설정 및 OOTP 세이브 위치 관리")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)

        # Save Location Group
        save_group = QGroupBox("OOTP 세이브 선택")
        save_layout = QVBoxLayout(save_group)

        # Dropdown for detected saves
        det_layout = QHBoxLayout()
        det_layout.addWidget(QLabel("자동 탐색된 세이브 목록:"))
        self.detected_combo = QComboBox()
        self.detected_combo.currentIndexChanged.connect(self._on_detected_selected)
        det_layout.addWidget(self.detected_combo, 1)
        save_layout.addLayout(det_layout)

        # Manual path entry
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("활성 세이브 폴더 (.lg):"))
        self.path_input = QLineEdit()
        path_layout.addWidget(self.path_input, 1)

        self.browse_btn = QPushButton("찾아보기...")
        self.browse_btn.clicked.connect(self._browse_save_path)
        path_layout.addWidget(self.browse_btn)

        save_layout.addLayout(path_layout)
        layout.addWidget(save_group)

        # Readiness Display
        readiness_group = QGroupBox("데이터 준비 상태 (Readiness)")
        read_layout = QVBoxLayout(readiness_group)

        self.readiness_status = QLabel("확인 중...")
        self.readiness_status.setStyleSheet("font-size: 13px; font-weight: bold;")
        read_layout.addWidget(self.readiness_status)

        self.path_details = QLabel("")
        self.path_details.setStyleSheet("color: #a0a0b0; font-size: 11px;")
        read_layout.addWidget(self.path_details)

        layout.addWidget(readiness_group)

        # Preferences Group
        pref_group = QGroupBox("기본 환경설정")
        pref_layout = QVBoxLayout(pref_group)

        season_layout = QHBoxLayout()
        season_layout.addWidget(QLabel("현재 시즌:"))
        self.season_input = QLineEdit()
        season_layout.addWidget(self.season_input)
        pref_layout.addLayout(season_layout)

        self.auto_watch_cb = QCheckBox("OOTP 실행 중 실시간 박스스코어 자동 가져오기 (Live Auto-Watch)")
        pref_layout.addWidget(self.auto_watch_cb)

        layout.addWidget(pref_group)

        # Save Button
        save_btn_layout = QHBoxLayout()
        save_btn_layout.addStretch()
        self.save_btn = QPushButton("설정 저장 적용")
        self.save_btn.setObjectName("accentButton")
        self.save_btn.clicked.connect(self._save_settings)
        save_btn_layout.addWidget(self.save_btn)

        layout.addLayout(save_btn_layout)
        layout.addStretch()

    def _load_values(self):
        self.path_input.setText(self.settings.active_save_path)
        self.season_input.setText(str(self.settings.current_season))
        self.auto_watch_cb.setChecked(self.settings.auto_watch_enabled)

        # Populate detected saves
        readiness = self.settings_mgr.check_readiness(self.settings)
        detected = readiness.get("detected_saves", [])

        self.detected_combo.clear()
        self.detected_combo.addItem("-- 자동 탐색된 OOTP 세이브 선택 --", "")
        for s in detected:
            self.detected_combo.addItem(os.path.basename(s), s)

        self._update_readiness_ui(readiness)

    def _on_detected_selected(self, index):
        selected_path = self.detected_combo.currentData()
        if selected_path:
            self.path_input.setText(selected_path)

    def _browse_save_path(self):
        folder = QFileDialog.getExistingDirectory(self, "OOTP 세이브 폴더 (.lg) 선택", self.path_input.text() or os.path.expanduser("~"))
        if folder:
            self.path_input.setText(folder)

    def _update_readiness_ui(self, readiness):
        if readiness["is_ready"]:
            self.readiness_status.setText("🟢 준비 완료: OOTP 박스스코어 및 데이터 접근 가능")
            self.readiness_status.setStyleSheet("color: #00e676; font-weight: bold;")
        else:
            self.readiness_status.setText("🔴 미완료: OOTP 세이브 경로를 지정해 주세요.")
            self.readiness_status.setStyleSheet("color: #ff5252; font-weight: bold;")

        details = f"Save Key: {readiness['save_key']} | DB: {readiness['db_path']}"
        self.path_details.setText(details)

    def _save_settings(self):
        self.settings.active_save_path = self.path_input.text().strip()
        try:
            self.settings.current_season = int(self.season_input.text().strip())
        except ValueError:
            self.settings.current_season = 2026

        self.settings.auto_watch_enabled = self.auto_watch_cb.isChecked()
        self.settings_mgr.save(self.settings)

        readiness = self.settings_mgr.check_readiness(self.settings)
        self._update_readiness_ui(readiness)

        QMessageBox.information(self, "설정 저장", "설정이 성공적으로 저장되었습니다.")
        if self.on_settings_changed:
            self.on_settings_changed(self.settings)
