from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget


class ToolsPage(QWidget):
    def __init__(self, repo, database, on_data_changed):
        super().__init__()
        self.repo = repo
        self.database = database
        self.on_data_changed = on_data_changed

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(8)

        title = QLabel("Developer & utility tools")
        title.setObjectName("sectionTitle")
        note = QLabel("Parser-facing tools will be added here after the OOTP save format is connected.")
        note.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(note)

        open_db = QPushButton("Open runtime data folder")
        open_db.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.database.path.parent))))
        reset = QPushButton("Reset generated sample database")
        reset.clicked.connect(self._reset_sample)
        layout.addWidget(open_db)
        layout.addWidget(reset)
        layout.addStretch(1)

    def _reset_sample(self):
        answer = QMessageBox.question(
            self,
            "Reset sample database",
            "Delete the local runtime DB and recreate the generated sample data?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.database.reset_sample()
            self.on_data_changed()
