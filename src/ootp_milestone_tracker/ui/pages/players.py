from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QScrollArea, QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from ...core.milestone_catalog import milestone_ladder
from ..widgets import MilestoneGauge, MilestoneLadderGauge


class PlayersPage(QWidget):
    def __init__(self, repo):
        super().__init__()
        self.repo = repo
        self.current_player_id = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        left = QFrame()
        left.setMinimumWidth(210)
        left.setMaximumWidth(300)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 14, 8, 14)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search players...")
        self.list = QListWidget()
        left_layout.addWidget(self.search)
        left_layout.addWidget(self.list, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(18, 16, 18, 18)
        right_layout.setSpacing(10)
        self.name = QLabel("Select a player")
        self.name.setObjectName("pageTitle")
        self.meta = QLabel("")
        self.meta.setObjectName("muted")
        right_layout.addWidget(self.name)
        right_layout.addWidget(self.meta)

        self.tabs = QTabWidget()
        self.stats_tab = QWidget()
        stats_layout = QVBoxLayout(self.stats_tab)
        stats_layout.setContentsMargins(0, 8, 0, 0)
        self.career = QLabel("")
        self.career.setObjectName("sectionTitle")
        self.stats_table = QTableWidget(0, 1)
        self.stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.verticalHeader().setDefaultSectionSize(29)
        stats_layout.addWidget(self.career)
        stats_layout.addWidget(self.stats_table, 1)

        self.milestone_tab = QScrollArea()
        self.milestone_tab.setWidgetResizable(True)
        self.milestone_body = QWidget()
        self.milestone_layout = QVBoxLayout(self.milestone_body)
        self.milestone_layout.setContentsMargins(2, 8, 8, 8)
        self.milestone_layout.setSpacing(3)
        self.milestone_layout.addStretch(1)
        self.milestone_tab.setWidget(self.milestone_body)

        self.awards_tab = QWidget()
        awards_layout = QVBoxLayout(self.awards_tab)
        awards_layout.setContentsMargins(0, 8, 0, 0)
        self.awards_table = QTableWidget(0, 2)
        self.awards_table.setHorizontalHeaderLabels(["Season", "Award"])
        self.awards_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.awards_table.verticalHeader().setVisible(False)
        self.awards_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        awards_layout.addWidget(self.awards_table)

        self.tabs.addTab(self.stats_tab, "Season / Career")
        self.tabs.addTab(self.milestone_tab, "Milestones")
        self.tabs.addTab(self.awards_tab, "Awards")
        right_layout.addWidget(self.tabs, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([245, 900])

        self.search.textChanged.connect(self.refresh_players)
        self.list.currentItemChanged.connect(self._select_player)
        self.refresh_players()

    def refresh_players(self):
        selected = self.current_player_id
        self.list.blockSignals(True)
        self.list.clear()
        for row in self.repo.players(self.search.text()):
            prefix = "★ " if row["is_tracked"] else ""
            display = row["name_ko"] or row["name_en"]
            item = QListWidgetItem(f'{prefix}{display}   {row["position"]}\n   {row["short_name"]} · {row["name_en"]}')
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.list.addItem(item)
            if row["id"] == selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        if self.list.count() and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)

    def _select_player(self, current, previous=None):
        if not current:
            return
        self.current_player_id = int(current.data(Qt.ItemDataRole.UserRole))
        self.refresh_detail()

    def refresh_detail(self):
        if not self.current_player_id:
            return
        player = self.repo.player(self.current_player_id)
        if not player:
            return
        self.name.setText(player["name_ko"] or player["name_en"])
        self.meta.setText(f'{player["name_en"]}  ·  {player["team_name"]}  ·  {player["position"]}  ·  Age {player["age"]}')

        pitching = player["position"] in ("SP", "RP", "P")
        seasons = self.repo.pitching_seasons(player["id"]) if pitching else self.repo.batting_seasons(player["id"])
        if pitching:
            columns = ["Season", "G", "GS", "W", "L", "SV", "IP", "SO", "ERA", "WHIP", "WAR"]
            keys = ["season", "g", "gs", "w", "l", "sv", "ip", "so", "era", "whip", "war"]
            career_w = sum(r["w"] for r in seasons)
            career_so = sum(r["so"] for r in seasons)
            self.career.setText(f"Loaded sample seasons · W {career_w} · SO {career_so}")
        else:
            columns = ["Season", "G", "PA", "H", "HR", "RBI", "AVG", "OBP", "SLG", "SB", "WAR"]
            keys = ["season", "g", "pa", "h", "hr", "rbi", "avg", "obp", "slg", "sb", "war"]
            career_h = sum(r["h"] for r in seasons)
            career_hr = sum(r["hr"] for r in seasons)
            self.career.setText(f"Loaded sample seasons · H {career_h} · HR {career_hr}")

        self.stats_table.setColumnCount(len(columns))
        self.stats_table.setHorizontalHeaderLabels(columns)
        self.stats_table.setRowCount(len(seasons))
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        for r_idx, row in enumerate(seasons):
            for c_idx, key in enumerate(keys):
                value = row[key]
                if key in ("avg", "obp", "slg"):
                    text = f"{value:.3f}".lstrip("0")
                elif key in ("era", "whip", "war", "ip"):
                    text = f"{value:.2f}"
                else:
                    text = str(value)
                item = QTableWidgetItem(text)
                if c_idx > 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.stats_table.setItem(r_idx, c_idx, item)

        while self.milestone_layout.count() > 1:
            item = self.milestone_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        milestone_rows = self.repo.player_milestones(player["id"])
        rendered_ladders = set()
        for row in milestone_rows:
            ladder_key = (row["scope"], row["stat_key"])
            ladder = milestone_ladder(*ladder_key)
            if ladder:
                if ladder_key in rendered_ladders:
                    continue
                related_rows = [
                    candidate for candidate in milestone_rows
                    if (candidate["scope"], candidate["stat_key"]) == ladder_key
                ]
                current_value = max(float(candidate["current_value"]) for candidate in related_rows)
                gauge = MilestoneLadderGauge(
                    ladder["title"],
                    current_value,
                    ladder["thresholds"],
                    ladder["unit"],
                )
                self.milestone_layout.insertWidget(self.milestone_layout.count() - 1, gauge)
                rendered_ladders.add(ladder_key)
                continue

            self.milestone_layout.insertWidget(self.milestone_layout.count() - 1, MilestoneGauge(row))

        awards = self.repo.awards(player["id"])
        self.awards_table.setRowCount(len(awards))
        for i, award in enumerate(awards):
            self.awards_table.setItem(i, 0, QTableWidgetItem(str(award["season"])))
            self.awards_table.setItem(i, 1, QTableWidgetItem(award["award_name"]))
