"""
Unit tests for Database & Schema Management (Phase 1.1)
"""

import os
import shutil
import tempfile
import sqlite3
import pytest
from core.db.connection import DatabaseManager


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_empty_db_initialization(temp_dir):
    db_path = os.path.join(temp_dir, "test_records.db")
    db_mgr = DatabaseManager(db_path, save_key="save_alpha")
    db_mgr.initialize_database()

    assert os.path.exists(db_path)
    assert db_mgr.get_schema_version() == 1

    with db_mgr.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        expected = {
            "metadata", "saves", "teams", "players", "player_team_affiliations",
            "games", "batting_game_stats", "pitching_game_stats",
            "baseline_batting_stats", "baseline_pitching_stats",
            "milestone_events", "manual_events", "streak_states",
            "streak_events", "processed_sources", "import_workflow_state"
        }
        assert expected.issubset(tables)


def test_schema_re_execution_idempotency(temp_dir):
    db_path = os.path.join(temp_dir, "test_records.db")
    db_mgr = DatabaseManager(db_path, save_key="save_alpha")
    db_mgr.initialize_database()

    # Re-run initialization to ensure no crash or corrupt tables
    db_mgr.initialize_database()
    assert db_mgr.get_schema_version() == 1


def test_save_isolation(temp_dir):
    db_path_a = os.path.join(temp_dir, "save_a", "records.db")
    db_path_b = os.path.join(temp_dir, "save_b", "records.db")

    mgr_a = DatabaseManager(db_path_a, save_key="save_a_key")
    mgr_b = DatabaseManager(db_path_b, save_key="save_b_key")

    mgr_a.initialize_database()
    mgr_b.initialize_database()

    # Insert player in DB A
    with mgr_a.get_connection() as conn_a:
        conn_a.execute(
            "INSERT INTO players (ootp_player_id, first_name, last_name, display_name) VALUES (?, ?, ?, ?)",
            (1001, "Mike", "Trout", "Mike Trout")
        )
        conn_a.commit()

    # Verify DB B is unaffected
    with mgr_b.get_connection() as conn_b:
        cursor = conn_b.cursor()
        cursor.execute("SELECT COUNT(*) FROM players")
        count_b = cursor.fetchone()[0]
        assert count_b == 0

    # Verify DB A has player
    with mgr_a.get_connection() as conn_a:
        cursor = conn_a.cursor()
        cursor.execute("SELECT display_name FROM players WHERE ootp_player_id = 1001")
        name = cursor.fetchone()[0]
        assert name == "Mike Trout"
