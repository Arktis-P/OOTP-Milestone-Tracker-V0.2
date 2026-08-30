from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from .pages.dashboard import DashboardPage
from .pages.milestones import MilestonesPage
from .pages.players import PlayersPage
from .pages.settings import SettingsPage
from .pages.tools import ToolsPage


class MainWindow(QMainWindow):
    def __init__(self, repo, database, theme_callback):
        super().__init__()
        self.repo = repo
        self.database = database
        self.theme_callback = theme_callback
        self.setWindowTitle("OOTP Milestone Tracker")
        self.resize(1180, 760)
        self.setMinimumSize(920, 620)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(154)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(8, 10, 8, 10)
        side_layout.setSpacing(3)

        brand = QLabel("OOTP\nTRACKER")
        brand.setObjectName("sectionTitle")
        brand.setContentsMargins(8, 4, 4, 12)
        side_layout.addWidget(brand)

        self.stack = QStackedWidget()
        self.dashboard = DashboardPage(repo)
        self.milestones = MilestonesPage(repo)
        self.players = PlayersPage(repo)
        self.tools = ToolsPage(repo, database, self.refresh_all)
        self.settings = SettingsPage(repo, self.refresh_all, self.theme_callback)
        self.pages = [self.dashboard, self.milestones, self.players, self.tools, self.settings]
        for page in self.pages:
            self.stack.addWidget(page)

        labels = ["Dashboard", "Milestones", "Player Records", "Tools", "Settings"]
        icons = ["▦", "▤", "♙", "◇", "⚙"]
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for idx, (icon, label) in enumerate(zip(icons, labels)):
            button = QPushButton(f"{icon}   {label}")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=idx: self._navigate(i))
            self.nav_group.addButton(button, idx)
            side_layout.addWidget(button)
            if idx == 0:
                button.setChecked(True)
        side_layout.addStretch(1)
        version = QLabel("Sample DB · v0.1")
        version.setObjectName("muted")
        version.setContentsMargins(8, 4, 0, 2)
        side_layout.addWidget(version)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(48)
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(18, 0, 14, 0)
        self.page_title = QLabel(labels[0])
        self.page_title.setObjectName("pageTitle")
        self.context = QLabel("")
        self.context.setObjectName("muted")
        refresh = QPushButton("↻  Refresh")
        refresh.clicked.connect(self.refresh_all)
        top_layout.addWidget(self.page_title)
        top_layout.addSpacing(12)
        top_layout.addWidget(self.context)
        top_layout.addStretch(1)
        top_layout.addWidget(refresh)
        content_layout.addWidget(topbar)
        content_layout.addWidget(self.stack, 1)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)
        self._labels = labels
        self._update_context()

    def _navigate(self, index: int):
        self.stack.setCurrentIndex(index)
        self.page_title.setText(self._labels[index])
        page = self.pages[index]
        if hasattr(page, "refresh"):
            page.refresh()

    def _update_context(self):
        team = self.repo.tracked_team()
        self.context.setText(f'Tracking: {team["name"]}' if team else "No tracked team")

    def refresh_all(self):
        self._update_context()
        for page in (self.dashboard, self.milestones, self.players, self.settings):
            if hasattr(page, "refresh"):
                page.refresh()
            elif hasattr(page, "refresh_players"):
                page.refresh_players()
        self.players.refresh_players()
