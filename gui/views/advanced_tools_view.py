"""
Advanced Tools View (Phase 14)
Power user tools: single boxscore recovery, Spring Training purging, Season Isolation Validation, DB reset.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QFileDialog, QMessageBox, QTextEdit
)
from core.config.settings import SettingsManager
from core.db.connection import DatabaseManager
from core.import_workflow.boxscore_import import BoxscoreImportService
from core.validation.season_validator import SeasonValidator


class AdvancedToolsView(QWidget):
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

        title = QLabel("Advanced Tools (고급 관리자 / 복구 도구)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Recovery Group
        rec_group = QGroupBox("복구 및 검증 액션")
        rec_layout = QVBoxLayout(rec_group)

        self.reimport_btn = QPushButton("1. 개별 박스스코어 재import 복구")
        self.reimport_btn.clicked.connect(self._reimport_single_boxscore)
        rec_layout.addWidget(self.reimport_btn)

        self.val_btn = QPushButton("2. 시즌 격리 검증 (Season Replay Validation)")
        self.val_btn.setObjectName("accentButton")
        self.val_btn.clicked.connect(self._run_season_validation)
        rec_layout.addWidget(self.val_btn)

        layout.addWidget(rec_group)

        # Danger Group
        danger_group = QGroupBox("위험 / 초기화 작업")
        danger_layout = QVBoxLayout(danger_group)

        self.reset_btn = QPushButton("현재 세이브 DB 초기화 (Clear Database)")
        self.reset_btn.setStyleSheet("background-color: #d32f2f; color: #ffffff; font-weight: bold;")
        self.reset_btn.clicked.connect(self._reset_current_db)
        danger_layout.addWidget(self.reset_btn)

        layout.addWidget(danger_group)

        # Log Console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

    def _reimport_single_boxscore(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "복구할 박스스코어 HTML 선택", self.paths.boxscores_dir, "HTML Files (*.html)")
        if not file_path:
            return

        try:
            db_mgr = DatabaseManager(self.paths.db_path)
            db_mgr.initialize_database()
            with db_mgr.get_connection() as conn:
                svc = BoxscoreImportService(conn)
                res = svc.import_boxscore(file_path, force_reimport=True)
                self.console.append(f"✅ [개별 복구 완료] {res['source_id']} 강제 재import 성공.")
                QMessageBox.information(self, "완료", f"박스스코어 재import가 완료되었습니다:\n{res['source_id']}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"재import 중 오류 발생:\n{e}")

    def _run_season_validation(self):
        if not os.path.exists(self.paths.boxscores_dir):
            QMessageBox.warning(self, "경로 없음", f"박스스코어 디렉터리가 필요합니다:\n{self.paths.boxscores_dir}")
            return

        self.console.append("🔄 별도 validation.db에서 시즌 검증 격리 Replay를 실행 중입니다...")
        try:
            validator = SeasonValidator(
                operating_db_path=self.paths.db_path,
                boxscores_dir=self.paths.boxscores_dir,
                import_export_dir=self.paths.import_export_dir
            )
            res = validator.validate_season(season=self.settings.current_season)

            match_text = "일치 (Match)" if res["is_match"] else "불일치 (Mismatch)"
            log_str = (
                f"✅ [시즌 격리 검증 결과: {match_text}]\n"
                f"• 검증 경기 수: {res['validation_game_count']} (운영 DB: {res['operating_game_count']})\n"
                f"• 검증 마일스톤 수: {res['validation_milestone_count']} (운영 DB: {res['operating_milestone_count']})"
            )
            self.console.append(log_str)
            QMessageBox.information(self, "검증 완료", f"시즌 격리 검증 완료!\n결과: {match_text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"격리 검증 중 오류 발생:\n{e}")

    def _reset_current_db(self):
        reply = QMessageBox.question(
            self,
            "명시적 초기화 확인",
            f"정말로 현재 세이브 DB를 완전히 초기화하시겠습니까?\n\n대상 DB: {self.paths.db_path}\n모든 마일스톤 및 가져오기 기록이 삭제됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if os.path.exists(self.paths.db_path):
                os.remove(self.paths.db_path)
            db_mgr = DatabaseManager(self.paths.db_path)
            db_mgr.initialize_database()
            self.console.append("🗑️ 현재 세이브 DB가 완전히 초기화되었습니다.")
            QMessageBox.information(self, "초기화 완료", "DB가 성공적으로 초기화되었습니다.")
