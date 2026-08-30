from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from ...services.season_service import SeasonService


class FinalizeSeasonDialog(QDialog):
    def __init__(self, repo, season: int = 2027, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.season = season
        self.season_service = SeasonService(repo.database)

        self.setWindowTitle(f"Finalize Regular Season {season}")
        self.setMinimumWidth(450)

        tracked = self.repo.tracked_team()
        self.tracked_team_id = tracked["id"] if tracked else 0
        self.team_name = tracked["name"] if tracked else "Unknown Team"

        self.processed, self.target, self.is_eligible = self.season_service.check_finalization_eligibility(
            self.season, self.tracked_team_id
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header Info
        info_label = QLabel(
            f"<b>Season:</b> {self.season}<br>"
            f"<b>Team:</b> {self.team_name}<br>"
            f"<b>Progress:</b> {self.processed} / {self.target} games processed"
        )
        layout.addWidget(info_label)

        # Export Check Status
        self.export_status_label = QLabel()
        layout.addWidget(self.export_status_label)

        self.check_export_files()

        # Action Buttons
        btn_layout = QHBoxLayout()

        self.recheck_btn = QPushButton("Recheck Export")
        self.recheck_btn.clicked.connect(self.check_export_files)
        btn_layout.addWidget(self.recheck_btn)

        btn_layout.addStretch()

        self.continue_btn = QPushButton("Continue Without Export")
        self.continue_btn.clicked.connect(self.on_continue_without_export)
        btn_layout.addWidget(self.continue_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.finalize_btn = QPushButton("Finalize with Export")
        self.finalize_btn.setDefault(True)
        self.finalize_btn.clicked.connect(self.on_finalize_with_export)
        btn_layout.addWidget(self.finalize_btn)

        layout.addLayout(btn_layout)

    def get_export_dir(self) -> Optional[Path]:
        save_path = self.repo.get_setting("lg_save_path", "")
        if save_path:
            p = Path(save_path) / "import_export"
            if p.exists():
                return p

        # Default fallback path if setting not set
        fallback = Path(
            r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg\import_export"
        )
        return fallback if fallback.exists() else None

    def check_export_files(self):
        export_dir = self.get_export_dir()
        if export_dir:
            b_file = export_dir / "player_batting_stats.txt"
            p_file = export_dir / "player_pitching_stats.txt"
            if b_file.exists() and p_file.exists():
                self.export_status_label.setText(
                    f"<font color='green'><b>✓ OOTP Export Available:</b></font> {export_dir.name}"
                )
                self.finalize_btn.setEnabled(True)
                return

        self.export_status_label.setText(
            "<font color='#d9534f'><b>⚠ OOTP Export Recommended:</b></font><br>"
            "No fresh <i>player_batting_stats.txt</i> / <i>player_pitching_stats.txt</i> found in import_export folder.<br>"
            "Exporting Player Stats from OOTP is recommended before finalizing."
        )
        self.finalize_btn.setEnabled(False)

    def on_finalize_with_export(self):
        export_dir = self.get_export_dir()
        try:
            res = self.season_service.finalize_season(
                self.season, self.tracked_team_id, export_dir=export_dir
            )
            QMessageBox.information(
                self,
                "Season Finalized",
                f"<b>Regular Season {self.season} Finalized!</b><br><br>"
                f"Status: {res['status']}<br>"
                f"Players Reconciled: {res['players_reconciled']}<br>"
                f"Field Adjustments: {res['adjustments']}<br>"
                f"Final Rate Milestones: {res['rate_milestones']}",
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Finalization Error", str(e))

    def on_continue_without_export(self):
        try:
            res = self.season_service.finalize_season(
                self.season, self.tracked_team_id, continue_without_export=True
            )
            QMessageBox.information(
                self,
                "Season Finalized (Unreconciled)",
                f"<b>Regular Season {self.season} Finalized without Export!</b><br><br>"
                f"Status: {res['status']}<br>"
                f"Final Rate Milestones: {res['rate_milestones']}<br>"
                "You can perform a late reconciliation whenever OOTP stats exports are supplied.",
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Finalization Error", str(e))
