from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget,
)

from ..dialogs.finalize_season_dialog import FinalizeSeasonDialog
from ..dialogs.game_milestone_settings_dialog import GameMilestoneSettingsDialog
from ...services.season_service import SeasonService


class MilestonesPage(QWidget):
    def __init__(self, repo):
        super().__init__()
        self.repo = repo
        self.season_service = SeasonService(repo.database)
        self.active_season = 2027

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(10)

        # Action & Control Bar
        control_bar = QHBoxLayout()
        self.season_status_label = QLabel()
        control_bar.addWidget(self.season_status_label)
        control_bar.addStretch()

        self.finalize_btn = QPushButton("Finalize Regular Season")
        self.finalize_btn.clicked.connect(self.open_finalize_dialog)
        control_bar.addWidget(self.finalize_btn)

        layout.addLayout(control_bar)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search player, team, milestone...")
        self.scope = QComboBox()
        self.scope.addItem("All scopes", "")
        for value in ("game", "season", "career", "award"):
            self.scope.addItem(value.title(), value)
        self.visibility = QComboBox()
        self.visibility.addItem("Tracked team only", True)
        self.visibility.addItem("All teams", False)
        filters.addWidget(self.search, 1)
        filters.addWidget(self.scope)
        filters.addWidget(self.visibility)
        layout.addLayout(filters)

        self.tabs = QTabWidget()

        # Tab 1: Milestone Targets
        self.targets_tab = QWidget()
        targets_layout = QVBoxLayout(self.targets_tab)
        targets_layout.setContentsMargins(0, 8, 0, 0)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Entity", "Team", "Scope", "Milestone", "Current", "Target", "Progress"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(29)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for col in (0, 1, 2, 4, 5, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        targets_layout.addWidget(self.table)

        # Tab 2: Game Achievements
        self.achievements_tab = QWidget()
        ach_layout = QVBoxLayout(self.achievements_tab)
        ach_layout.setContentsMargins(0, 8, 0, 0)

        ach_top_bar = QHBoxLayout()
        ach_top_bar.addStretch()
        self.settings_btn = QPushButton("Game Milestone Settings")
        self.settings_btn.clicked.connect(self.open_settings_dialog)
        ach_top_bar.addWidget(self.settings_btn)
        ach_layout.addLayout(ach_top_bar)

        self.ach_table = QTableWidget(0, 6)
        self.ach_table.setHorizontalHeaderLabels(["Date", "Player", "Competition", "Milestone", "Opponent/Game", "Context"])
        self.ach_table.setAlternatingRowColors(True)
        self.ach_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ach_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ach_table.setSortingEnabled(True)
        self.ach_table.verticalHeader().setVisible(False)
        self.ach_table.verticalHeader().setDefaultSectionSize(29)
        ach_header = self.ach_table.horizontalHeader()
        ach_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        ach_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        for col in (0, 1, 2, 4):
            ach_header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        ach_layout.addWidget(self.ach_table)

        # Tab 3: Season Achievements
        self.season_ach_tab = QWidget()
        season_ach_layout = QVBoxLayout(self.season_ach_tab)
        season_ach_layout.setContentsMargins(0, 8, 0, 0)

        self.season_ach_table = QTableWidget(0, 7)
        self.season_ach_table.setHorizontalHeaderLabels(["Date", "Player/Team", "Season", "Competition", "Milestone", "Value", "Source"])
        self.season_ach_table.setAlternatingRowColors(True)
        self.season_ach_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.season_ach_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.season_ach_table.setSortingEnabled(True)
        self.season_ach_table.verticalHeader().setVisible(False)
        self.season_ach_table.verticalHeader().setDefaultSectionSize(29)
        s_header = self.season_ach_table.horizontalHeader()
        s_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for col in (0, 1, 2, 3, 5, 6):
            s_header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        season_ach_layout.addWidget(self.season_ach_table)

        self.tabs.addTab(self.targets_tab, "Milestone Targets")
        self.tabs.addTab(self.achievements_tab, "Game Achievements")
        self.tabs.addTab(self.season_ach_tab, "Season Achievements")
        layout.addWidget(self.tabs, 1)

        self.search.textChanged.connect(self.refresh)
        self.scope.currentIndexChanged.connect(self.refresh)
        self.visibility.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def open_settings_dialog(self):
        dialog = GameMilestoneSettingsDialog(self.repo, self)
        if dialog.exec():
            self.refresh()

    def open_finalize_dialog(self):
        dialog = FinalizeSeasonDialog(self.repo, self.active_season, self)
        if dialog.exec():
            self.refresh()

    def update_control_bar(self):
        tracked = self.repo.tracked_team()
        tid = tracked["id"] if tracked else 0
        processed, target, is_eligible = self.season_service.check_finalization_eligibility(self.active_season, tid)

        state = self.repo.current_season_state(self.active_season)
        status_str = state["status"] if state else ("Ready to finalize" if is_eligible else "In Progress")

        self.season_status_label.setText(
            f"<b>Regular Season {self.active_season}</b> · {processed} / {target} games processed · <i>{status_str}</i>"
        )
        self.finalize_btn.setEnabled(is_eligible or (state and state["status"].startswith("finalized")))

    def refresh(self):
        self.update_control_bar()

        # 1. Targets table
        rows = self.repo.milestones(
            tracked_only=bool(self.visibility.currentData()),
            scope=str(self.scope.currentData() or ""),
            search=self.search.text(),
        )
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            values = [
                row["entity_name"], row["team_name"] or "-", row["scope"].title(), row["label"],
                f'{row["current_value"]:,.0f}', f'{row["target_value"]:,.0f}', f'{row["progress"]:.1f}%',
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, row["id"])
                if col >= 4:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, col, item)
        self.table.setSortingEnabled(True)

        # 2. Game Achievements table
        ach_rows = self.repo.game_milestone_achievements(
            tracked_only=bool(self.visibility.currentData())
        )
        self.ach_table.setSortingEnabled(False)
        self.ach_table.setRowCount(len(ach_rows))
        for i, row in enumerate(ach_rows):
            game_vs = f'{row["away_team_short"]} @ {row["home_team_short"]}'
            values = [
                row["game_date"],
                row["player_name"],
                row["competition_type"].replace("_", " ").title(),
                row["title"],
                game_vs,
                row["context_text"] or "-",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                self.ach_table.setItem(i, col, item)
        self.ach_table.setSortingEnabled(True)

        # 3. Season Achievements table
        s_rows = self.repo.season_milestone_achievements(
            tracked_only=bool(self.visibility.currentData())
        )
        self.season_ach_table.setSortingEnabled(False)
        self.season_ach_table.setRowCount(len(s_rows))
        for i, row in enumerate(s_rows):
            val_str = f"{row['achieved_value']:.3f}" if "AVG" in row["rule_key"] or "OBP" in row["rule_key"] or "OPS" in row["rule_key"] or "ERA" in row["rule_key"] else f"{row['achieved_value']:,.0f}"
            values = [
                row["achieved_date"] or "Season Final",
                row["entity_name"],
                str(row["season"]),
                row["competition_type"].replace("_", " ").title(),
                row["title"],
                val_str,
                row["source"],
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                self.season_ach_table.setItem(i, col, item)
        self.season_ach_table.setSortingEnabled(True)
