from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QHeaderView, QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


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
        layout.addWidget(self.table, 1)

        self.search.textChanged.connect(self.refresh)
        self.scope.currentIndexChanged.connect(self.refresh)
        self.visibility.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
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
