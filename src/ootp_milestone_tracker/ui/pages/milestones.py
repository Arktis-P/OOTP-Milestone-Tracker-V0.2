from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLineEdit, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget,
)


class MilestonesPage(QWidget):
    def __init__(self, repo):
        super().__init__()
        self.repo = repo
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(10)

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

        self.tabs.addTab(self.targets_tab, "Milestone Targets")
        self.tabs.addTab(self.achievements_tab, "Game Achievements")
        layout.addWidget(self.tabs, 1)

        self.search.textChanged.connect(self.refresh)
        self.scope.currentIndexChanged.connect(self.refresh)
        self.visibility.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
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
