import sys

from PySide6.QtWidgets import QApplication

from .core.paths import DEFAULT_DB_PATH, ensure_runtime_dirs
from .db.database import Database
from .db.repository import Repository
from .ui.main_window import MainWindow
from .ui.theme import apply_theme


def main() -> int:
    ensure_runtime_dirs()
    database = Database(DEFAULT_DB_PATH)
    database.initialize()
    repo = Repository(database)

    app = QApplication(sys.argv)
    app.setApplicationName("OOTP Milestone Tracker")
    app.setOrganizationName("Arktis-P")

    def change_theme(theme: str) -> None:
        apply_theme(app, theme)

    change_theme(repo.get_setting("theme", "dark"))
    window = MainWindow(repo, database, change_theme)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
