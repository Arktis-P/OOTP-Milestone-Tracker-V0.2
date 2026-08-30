from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt

from ...importer.source_locator import default_league_save, saved_games_roots


class SettingsPage(QWidget):
    def __init__(self, repo, on_data_changed, on_theme_changed):
        super().__init__()
        self.repo = repo
        self.on_data_changed = on_data_changed
        self.on_theme_changed = on_theme_changed

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(14)

        general_title = QLabel("Data & tracking")
        general_title.setObjectName("sectionTitle")
        layout.addWidget(general_title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        save_row = QHBoxLayout()
        self.save_folder = QLineEdit()
        detect = QPushButton("Auto-detect")
        detect.clicked.connect(self._autodetect)
        browse = QPushButton("Browse")
        browse.clicked.connect(self._browse)
        save_row.addWidget(self.save_folder, 1)
        save_row.addWidget(detect)
        save_row.addWidget(browse)
        form.addRow("OOTP .lg save", save_row)

        path_note = QLabel("Auto-detect resolves the current Windows Documents location, including redirected OneDrive Documents folders.")
        path_note.setObjectName("muted")
        form.addRow("", path_note)

        self.team = QComboBox()
        form.addRow("Tracked team", self.team)
        self.theme = QComboBox()
        self.theme.addItem("Dark", "dark")
        self.theme.addItem("Light", "light")
        form.addRow("Theme", self.theme)
        layout.addLayout(form)

        save_button = QPushButton("Save settings")
        save_button.setObjectName("primary")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignLeft)

        names_title = QLabel("Player name mapping")
        names_title.setObjectName("sectionTitle")
        names_note = QLabel("Korean display names are stored against the internal player ID, not the English string.")
        names_note.setObjectName("muted")
        layout.addWidget(names_title)
        layout.addWidget(names_note)
        self.names = QTableWidget(0, 3)
        self.names.setHorizontalHeaderLabels(["Player ID", "English", "Korean display"])
        self.names.horizontalHeader().setStretchLastSection(True)
        self.names.verticalHeader().setVisible(False)
        layout.addWidget(self.names, 1)
        map_save = QPushButton("Save name mappings")
        map_save.clicked.connect(self.save_mappings)
        layout.addWidget(map_save, alignment=Qt.AlignmentFlag.AlignLeft)

        self.refresh()

    def _autodetect(self):
        detected = default_league_save()
        if detected:
            self.save_folder.setText(str(detected))

    def _browse(self):
        start = self.save_folder.text().strip()
        if not start:
            roots = saved_games_roots()
            start = str(next((path for path in roots if path.is_dir()), roots[0] if roots else ""))
        path = QFileDialog.getExistingDirectory(self, "Select OOTP .lg save folder", start)
        if path:
            self.save_folder.setText(path)

    def refresh(self):
        saved = self.repo.get_setting("save_folder", "")
        if saved:
            self.save_folder.setText(saved)
        else:
            self._autodetect()

        self.team.clear()
        tracked_id = None
        for row in self.repo.teams():
            self.team.addItem(row["name"], row["id"])
            if row["is_tracked"]:
                tracked_id = row["id"]
        if tracked_id is not None:
            index = self.team.findData(tracked_id)
            if index >= 0:
                self.team.setCurrentIndex(index)
        theme = self.repo.get_setting("theme", "dark")
        index = self.theme.findData(theme)
        self.theme.setCurrentIndex(max(index, 0))

        players = self.repo.players()
        self.names.setRowCount(len(players))
        for i, player in enumerate(players):
            id_item = QTableWidgetItem(str(player["id"]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            en_item = QTableWidgetItem(player["name_en"])
            en_item.setFlags(en_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            ko_item = QTableWidgetItem(player["name_ko"] or "")
            self.names.setItem(i, 0, id_item)
            self.names.setItem(i, 1, en_item)
            self.names.setItem(i, 2, ko_item)

    def save(self):
        self.repo.set_setting("save_folder", self.save_folder.text().strip())
        self.repo.set_setting("theme", str(self.theme.currentData()))
        if self.team.currentData() is not None:
            self.repo.set_tracked_team(int(self.team.currentData()))
        self.on_theme_changed(str(self.theme.currentData()))
        self.on_data_changed()

    def save_mappings(self):
        for row in range(self.names.rowCount()):
            player_id = int(self.names.item(row, 0).text())
            value = self.names.item(row, 2).text() if self.names.item(row, 2) else ""
            self.repo.update_name_mapping(player_id, value)
        self.on_data_changed()
