from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView

from ..widgets import StatBox


class DashboardPage(QWidget):
    def __init__(self, repo):
        super().__init__()
        self.repo = repo
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(14)

        self.team_label = QLabel("Tracking")
        self.team_label.setObjectName("muted")
        layout.addWidget(self.team_label)

        stats = QHBoxLayout()
        stats.setSpacing(8)
        self.players_box = StatBox("Tracked players")
        self.milestones_box = StatBox("Milestones")
        self.near_box = StatBox("90%+ near")
        for box in (self.players_box, self.milestones_box, self.near_box):
            stats.addWidget(box)
        stats.addStretch(1)
        layout.addLayout(stats)

        title = QLabel("Next milestones")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Entity", "Scope", "Milestone", "Current / Target", "Progress"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(29)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 1)

        self.refresh()

    def refresh(self):
        summary = self.repo.dashboard_summary()
        self.team_label.setText(f'TRACKING · {summary["team"]}')
        self.players_box.set_value(summary["players"])
        self.milestones_box.set_value(summary["milestones"])
        self.near_box.set_value(summary["near"])

        rows = [r for r in self.repo.milestones(tracked_only=True) if not r["achieved"]][:8]
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            values = [
                row["entity_name"], row["scope"].title(), row["label"],
                f'{row["current_value"]:,.0f} / {row["target_value"]:,.0f}', f'{row["progress"]:.1f}%',
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col in (3, 4):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, col, item)
