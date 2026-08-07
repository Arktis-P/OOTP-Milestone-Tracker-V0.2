"""
Live Directory Auto-Watch Service (Phase 3.4)
Monitors OOTP save boxscores/ and news/ folders in the background for new or modified files.
Opens dedicated SQLite thread connections to remain thread-safe.
"""

import os
import glob
import time
import threading
from typing import Callable, Optional, Dict, Any
from core.db.connection import DatabaseManager
from core.import_workflow.boxscore_import import BoxscoreImportService


class LiveAutoWatcher:
    def __init__(
        self,
        boxscores_dir: str,
        db_path: str,
        on_import_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        poll_interval: float = 0.5
    ):
        self.boxscores_dir = boxscores_dir
        self.db_path = db_path
        self.on_import_callback = on_import_callback
        self.poll_interval = poll_interval

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_mtimes: Dict[str, float] = {}

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def is_running(self) -> bool:
        return self._running

    def _run_loop(self) -> None:
        db_mgr = DatabaseManager(self.db_path)
        with db_mgr.get_connection() as conn:
            import_svc = BoxscoreImportService(conn)
            while self._running:
                if os.path.exists(self.boxscores_dir):
                    files = glob.glob(os.path.join(self.boxscores_dir, "game_box_*.html"))
                    for f_path in files:
                        try:
                            mtime = os.path.getmtime(f_path)
                            last_seen = self._file_mtimes.get(f_path)

                            if last_seen is None or mtime > last_seen:
                                res = import_svc.import_boxscore(f_path)
                                self._file_mtimes[f_path] = mtime
                                if res["status"] in ("success", "unchanged") and self.on_import_callback:
                                    self.on_import_callback(res)
                        except Exception:
                            pass
                time.sleep(self.poll_interval)
