"""
Record Import Center View (Phase 5.3)
Central UI hub for baseline stats import, boxscore batch import, and Live Auto-Watch toggle.
Uses QThread workers for non-blocking UI responsiveness.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QTextEdit, QProgressBar, QMessageBox
)
from PySide6.QtCore import QThread, Signal, Qt
from core.config.settings import SettingsManager
from core.db.connection import DatabaseManager
from core.import_workflow.baseline_import import BaselineImportService
from core.import_workflow.boxscore_import import BoxscoreImportService
from core.import_workflow.auto_watcher import LiveAutoWatcher


class BatchImportWorker(QThread):
    progress_signal = Signal(str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, db_path: str, boxscores_dir: str):
        super().__init__()
        self.db_path = db_path
        self.boxscores_dir = boxscores_dir

    def run(self):
        try:
            self.progress_signal.emit("박스스코어 일괄 가져오기를 시작합니다...")
            db_mgr = DatabaseManager(self.db_path)
            with db_mgr.get_connection() as conn:
                svc = BoxscoreImportService(conn)
                res = svc.import_boxscores_dir(self.boxscores_dir)
                self.finished_signal.emit(res)
        except Exception as e:
            self.error_signal.emit(str(e))


class RecordImportCenterView(QWidget):
    def __init__(self, settings_mgr: SettingsManager):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.settings = self.settings_mgr.load()
        self.paths = self.settings_mgr.get_derived_paths(self.settings)

        self.auto_watcher: Optional[LiveAutoWatcher] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Record Import Center (데이터 가져오기 센터)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Action Buttons Group
        actions_group = QGroupBox("가져오기 수동 작업")
        actions_layout = QHBoxLayout(actions_group)

        self.baseline_btn = QPushButton("1. Baseline Stats TXT 가져오기")
        self.baseline_btn.clicked.connect(self._run_baseline_import)
        actions_layout.addWidget(self.baseline_btn)

        self.boxscore_btn = QPushButton("2. 최신 박스스코어 일괄 가져오기")
        self.boxscore_btn.setObjectName("accentButton")
        self.boxscore_btn.clicked.connect(self._run_boxscore_batch_import)
        actions_layout.addWidget(self.boxscore_btn)

        self.watcher_btn = QPushButton("3. Live Auto-Watch 시작 (알림)")
        self.watcher_btn.clicked.connect(self._toggle_auto_watcher)
        actions_layout.addWidget(self.watcher_btn)

        layout.addWidget(actions_group)

        # Status & Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Log Console Group
        console_group = QGroupBox("가져오기 로그 콘솔")
        console_layout = QVBoxLayout(console_group)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        console_layout.addWidget(self.log_console)

        layout.addWidget(console_group)

    def _append_log(self, text: str):
        self.log_console.append(text)

    def _run_baseline_import(self):
        readiness = self.settings_mgr.check_readiness(self.settings)
        if not readiness["save_path_exists"]:
            QMessageBox.warning(self, "오류", "유효한 OOTP 세이브 경로가 지정되지 않았습니다.")
            return

        import_dir = self.paths.import_export_dir
        bat_file = os.path.join(import_dir, "player_batting_stats.txt")
        pitch_file = os.path.join(import_dir, "player_pitching_stats.txt")

        if not os.path.exists(bat_file) or not os.path.exists(pitch_file):
            QMessageBox.warning(self, "파일 없음", f"import_export 폴더에 통계 TXT 파일이 없습니다:\n{import_dir}")
            return

        try:
            db_mgr = DatabaseManager(self.paths.db_path)
            with db_mgr.get_connection() as conn:
                svc = BaselineImportService(conn)
                res = svc.import_baselines(bat_file, pitch_file, season=self.settings.current_season, mode="refresh")
                self._append_log(f"✅ [Baseline Import 완료] 타자: {res['batting_records_imported']}건, 투수: {res['pitching_records_imported']}건")
                QMessageBox.information(self, "완료", "Baseline 통계 가져오기가 성공적으로 완료되었습니다.")
        except Exception as e:
            self._append_log(f"❌ [Baseline Import 실패]: {e}")
            QMessageBox.critical(self, "오류", f"Baseline 가져오기 중 오류 발생:\n{e}")

    def _run_boxscore_batch_import(self):
        if not os.path.exists(self.paths.boxscores_dir):
            QMessageBox.warning(self, "경로 없음", f"박스스코어 디렉터리가 존재하지 않습니다:\n{self.paths.boxscores_dir}")
            return

        self.progress_bar.show()
        self.boxscore_btn.setEnabled(False)

        self.worker = BatchImportWorker(self.paths.db_path, self.paths.boxscores_dir)
        self.worker.progress_signal.connect(self._append_log)
        self.worker.finished_signal.connect(self._on_batch_finished)
        self.worker.error_signal.connect(self._on_batch_error)
        self.worker.start()

    def _on_batch_finished(self, res: dict):
        self.progress_bar.hide()
        self.boxscore_btn.setEnabled(True)
        self.log_console.append(
            f"✅ [박스스코어 가져오기 완료] 총 발견: {res['total_found']}건 | 신규: {res['imported']}건 | 변경없음: {res['unchanged']}건 | 오류: {res['errors_count']}건"
        )
        QMessageBox.information(self, "완료", f"박스스코어 {res['imported']}건 신규 가져오기 완료!")

    def _on_batch_error(self, err_msg: str):
        self.progress_bar.hide()
        self.boxscore_btn.setEnabled(True)
        self.log_console.append(f"❌ [박스스코어 가져오기 오류]: {err_msg}")

    def _toggle_auto_watcher(self):
        if self.auto_watcher and self.auto_watcher.is_running():
            self.auto_watcher.stop()
            self.watcher_btn.setText("3. Live Auto-Watch 시작 (알림)")
            self._append_log("⏹️ Live Auto-Watch 중지됨.")
        else:
            if not os.path.exists(self.paths.boxscores_dir):
                QMessageBox.warning(self, "경로 없음", f"박스스코어 감시 폴더가 없습니다:\n{self.paths.boxscores_dir}")
                return
            self.auto_watcher = LiveAutoWatcher(
                boxscores_dir=self.paths.boxscores_dir,
                db_path=self.paths.db_path,
                on_import_callback=lambda res: self._append_log(f"🔔 [실시간 라이브 가져오기] {res['source_id']} 처리 완료!")
            )
            self.auto_watcher.start()
            self.watcher_btn.setText("3. Live Auto-Watch 중지")
            self._append_log("▶️ Live Auto-Watch 실행 중... OOTP 새 경기 감지 시 자동 가져오기 수행.")
