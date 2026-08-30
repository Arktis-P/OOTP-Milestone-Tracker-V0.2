import sqlite3
from pathlib import Path

from .sample_seed import seed_sample_data
from .schema import SCHEMA_SQL


class Database:
    def __init__(self, path: Path):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
            count = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
            if count == 0:
                seed_sample_data(conn)
            conn.commit()

    def reset_sample(self) -> None:
        if self.path.exists():
            self.path.unlink()
        self.initialize()
