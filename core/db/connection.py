"""
Database Connection Manager & Schema Migration Engine
Implements save isolation, WAL mode, foreign key enforcement, and version tracking.
"""

import os
import sqlite3
import datetime
from typing import Optional
from core.db.schema import CURRENT_SCHEMA_VERSION, CREATE_TABLES_SQL


class DatabaseManager:
    def __init__(self, db_path: str, save_key: str = "default_save", save_path_snapshot: str = ""):
        self.db_path = os.path.abspath(db_path)
        self.save_key = save_key
        self.save_path_snapshot = save_path_snapshot
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def initialize_database(self) -> None:
        """Initializes tables and metadata if missing, or upgrades schema if version is old."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(CREATE_TABLES_SQL)

            # Check schema_version in metadata
            cursor.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
            row = cursor.fetchone()
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            if row is None:
                cursor.execute("INSERT INTO metadata (key, value) VALUES ('schema_version', ?)", (str(CURRENT_SCHEMA_VERSION),))
                cursor.execute("INSERT INTO metadata (key, value) VALUES ('created_at', ?)", (now_iso,))
                cursor.execute("INSERT INTO metadata (key, value) VALUES ('save_key', ?)", (self.save_key,))
                cursor.execute("INSERT INTO metadata (key, value) VALUES ('save_path_snapshot', ?)", (self.save_path_snapshot,))
                conn.commit()
            else:
                current_ver = int(row[0])
                if current_ver < CURRENT_SCHEMA_VERSION:
                    self._migrate(conn, current_ver, CURRENT_SCHEMA_VERSION)

    def _migrate(self, conn: sqlite3.Connection, from_version: int, to_version: int) -> None:
        """Performs incremental N -> N+1 schema migrations."""
        cursor = conn.cursor()
        for v in range(from_version, to_version):
            # Incremental migrations will be added here as schema grows
            pass
        cursor.execute("UPDATE metadata SET value = ? WHERE key = 'schema_version'", (str(to_version),))
        conn.commit()

    def get_schema_version(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
            row = cursor.fetchone()
            return int(row[0]) if row else 0
