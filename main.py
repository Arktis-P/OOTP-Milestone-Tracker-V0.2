"""
OOTP Milestone Tracker V0.2 Entrypoint.
"""

import sys
import argparse
from core.config.settings import SettingsManager


def main():
    parser = argparse.ArgumentParser(description="OOTP Milestone Tracker V0.2")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    args = parser.parse_args()

    print("Initializing OOTP Milestone Tracker V0.2...")
    settings_mgr = SettingsManager()
    settings = settings_mgr.load()
    readiness = settings_mgr.check_readiness(settings)

    print(f"Active Save: {settings.active_save_path or 'Not configured'}")
    print(f"Readiness: {readiness}")

    if args.cli:
        print("CLI Mode Bootstrap successfully completed.")
        return 0

    print("Starting GUI mode...")
    try:
        from PySide6.QtWidgets import QApplication
        from gui.theme.theme import apply_dark_theme
        from gui.views.main_window import MainWindow

        app = QApplication(sys.argv)
        apply_dark_theme(app)
        window = MainWindow(settings_mgr)
        window.show()
        print("GUI Window launched successfully.")
        return app.exec()
    except ImportError:
        print("PySide6 is not installed or GUI dependencies missing. Falling back to CLI mode.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
