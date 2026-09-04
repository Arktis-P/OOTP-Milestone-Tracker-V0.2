from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QMessageBox, QFormLayout, QGroupBox, QSpinBox
)
from PySide6.QtCore import Qt

from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.services.history_service import HistoryService
from ootp_milestone_tracker.services.history_renderer import render_manual_league_title_description, translate_league

BATTER_AWARDS = [
    ("AVG", "타격왕 (AVG)"),
    ("H", "안타왕 (H)"),
    ("OBP", "출루왕 (OBP)"),
    ("HR", "홈런왕 (HR)"),
    ("RBI", "타점왕 (RBI)"),
    ("SB", "도루왕 (SB)"),
    ("R", "득점왕 (R)"),
    ("OPS", "OPS 1위 (OPS)"),
]

PITCHER_AWARDS = [
    ("W", "다승왕 (W)"),
    ("ERA", "ERA 1위 (ERA)"),
    ("IP", "최다이닝 1위 (IP)"),
    ("SO", "탈삼진왕 (SO)"),
    ("SV", "구원왕 (SV)"),
    ("HOLD", "홀드왕 (HOLD)"),
    ("WPCT", "승률 1위 (WPCT)"),
]

class ManualAwardDialog(QDialog):
    def __init__(self, repo: Repository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.history_service = HistoryService(repo)
        self.setWindowTitle("수동 수상 기록 추가")
        self.resize(460, 380)

        self.players_list = self.repo.players()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        group = QGroupBox("리그 타이틀 수상 수동 입력")
        form = QFormLayout(group)

        # 1. Player Select
        self.player_combo = QComboBox()
        for p in self.players_list:
            display_name = f"{p.get('name_ko') or p.get('name_en')} ({p.get('team_name')}, {p.get('position')})"
            self.player_combo.addItem(display_name, userData=p['id'])
        self.player_combo.currentIndexChanged.connect(self.on_player_or_season_changed)
        form.addRow("선수 선택:", self.player_combo)

        # 2. Season Select
        self.season_spin = QSpinBox()
        self.season_spin.setRange(1900, 2030)
        self.season_spin.setValue(2027)
        self.season_spin.valueChanged.connect(self.on_player_or_season_changed)
        form.addRow("시즌 (연도):", self.season_spin)

        # 3. Award Type Select
        self.award_combo = QComboBox()
        self.populate_awards()
        self.award_combo.currentIndexChanged.connect(self.auto_fill_stat)
        form.addRow("수상 항목:", self.award_combo)

        # 4. League Override
        self.league_combo = QComboBox()
        self.league_combo.addItems(["AL", "NL", "KBO", "MLB"])
        self.league_combo.currentIndexChanged.connect(self.update_preview)
        form.addRow("리그 선택:", self.league_combo)

        # 5. Stat Value (Auto-filled / Manual Override)
        self.stat_input = QLineEdit()
        self.stat_input.setPlaceholderText("예: .369, 58, 0.98")
        self.stat_input.textChanged.connect(self.update_preview)
        form.addRow("기록 수치:", self.stat_input)

        # Preview
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("font-weight: bold; color: #2b5b84;")
        form.addRow("미리보기:", self.preview_label)

        layout.addWidget(group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("저장")
        self.save_btn.clicked.connect(self.on_save)
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.on_player_or_season_changed()

    def get_selected_player_id(self) -> Optional[int]:
        return self.player_combo.currentData()

    def on_player_or_season_changed(self):
        self.populate_awards()
        self.auto_fill_stat()

    def populate_awards(self):
        p_id = self.get_selected_player_id()
        if not p_id:
            return
        player = self.repo.player(p_id)
        pos = player.get("position", "") if player else ""

        self.award_combo.blockSignals(True)
        self.award_combo.clear()

        # Is pitcher?
        if pos in ("P", "SP", "RP", "CL"):
            for key, label in PITCHER_AWARDS:
                self.award_combo.addItem(label, userData=key)
        else:
            for key, label in BATTER_AWARDS:
                self.award_combo.addItem(label, userData=key)

        self.award_combo.blockSignals(False)

    def auto_fill_stat(self):
        p_id = self.get_selected_player_id()
        season = self.season_spin.value()
        award_key = self.award_combo.currentData()

        if not p_id or not award_key:
            return

        stat_val_str = ""
        batting_rows = self.repo.batting_seasons(p_id)
        pitching_rows = self.repo.pitching_seasons(p_id)

        target_bat = next((r for r in batting_rows if r['season'] == season), None)
        target_pitch = next((r for r in pitching_rows if r['season'] == season), None)

        if target_bat and award_key in target_bat:
            val = target_bat[award_key]
            if award_key in ('AVG', 'OBP', 'SLG', 'OPS'):
                stat_val_str = f"{val:.3f}".lstrip('0') if val < 1.0 else f"{val:.3f}"
            else:
                stat_val_str = str(int(val))
        elif target_pitch and award_key in target_pitch:
            val = target_pitch[award_key]
            if award_key in ('ERA', 'WHIP'):
                stat_val_str = f"{val:.2f}"
            elif award_key == 'IP':
                stat_val_str = f"{val:.1f}"
            elif award_key == 'WPCT':
                stat_val_str = f"{val:.3f}".lstrip('0')
            else:
                stat_val_str = str(int(val))

        self.stat_input.setText(stat_val_str)
        self.update_preview()

    def update_preview(self):
        award_key = self.award_combo.currentData()
        stat_val = self.stat_input.text().strip()
        league = self.league_combo.currentText()

        if not award_key or not stat_val:
            self.preview_label.setText("-")
            return

        desc = render_manual_league_title_description(award_key, stat_val, translate_league(league))
        self.preview_label.setText(desc)

    def on_save(self):
        p_id = self.get_selected_player_id()
        season = self.season_spin.value()
        award_key = self.award_combo.currentData()
        stat_val = self.stat_input.text().strip()
        league = self.league_combo.currentText()

        if not p_id or not award_key or not stat_val:
            QMessageBox.warning(self, "입력 오류", "모든 항목을 입력해주세요.")
            return

        success = self.history_service.add_manual_league_title_award(
            player_id=p_id,
            season=season,
            award_key=award_key,
            stat_value_str=stat_val,
            league_label=league
        )

        if success:
            QMessageBox.information(self, "저장 완료", "수동 수상 기록이 성공적으로 저장되었습니다.")
            self.accept()
        else:
            QMessageBox.critical(self, "저장 실패", "수상 기록 저장 중 오류가 발생했습니다.")
