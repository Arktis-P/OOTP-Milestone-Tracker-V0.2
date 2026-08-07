"""
Unit tests for Player Identity & Temporary Player Merging (Phase 1.2)
"""

import os
import shutil
import tempfile
import pytest
from core.db.connection import DatabaseManager
from core.db.player_repo import PlayerRepository


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_player_creation_and_lookup(temp_dir):
    db_path = os.path.join(temp_dir, "records.db")
    db_mgr = DatabaseManager(db_path)
    db_mgr.initialize_database()

    with db_mgr.get_connection() as conn:
        repo = PlayerRepository(conn)
        p1 = repo.get_or_create_player(1001, "Aaron", "Judge")
        p2 = repo.get_or_create_player(1001, "Aaron", "Judge")  # Same OOTP ID
        p_temp = repo.get_or_create_player(None, "Shohei", "Ohtani")

        assert p1["id"] == p2["id"]
        assert p1["is_temporary"] == 0
        assert p_temp["is_temporary"] == 1
        assert p_temp["ootp_player_id"] is None


def test_temporary_player_merge(temp_dir):
    db_path = os.path.join(temp_dir, "records.db")
    db_mgr = DatabaseManager(db_path)
    db_mgr.initialize_database()

    with db_mgr.get_connection() as conn:
        repo = PlayerRepository(conn)
        temp_p = repo.get_or_create_player(None, "Juan", "Soto")
        target_p = repo.get_or_create_player(9001, "Juan", "Soto")

        temp_id = temp_p["id"]
        target_id = target_p["id"]

        # Insert milestone event linked to temporary player
        conn.execute(
            """INSERT INTO milestone_events (policy_key, player_id, season, event_date, scope, category, grade, value, threshold, created_at)
               VALUES ('bat_career_hr_100', ?, 2026, '2026-05-01', 'career', 'batting', 'epic', 100, 100, '2026-05-01T00:00:00')""",
            (temp_id,)
        )
        conn.commit()

        # Execute merge
        success = repo.merge_temporary_player(temp_id, target_id)
        assert success is True

        # Verify event was re-linked to target_id
        cursor = conn.cursor()
        cursor.execute("SELECT player_id FROM milestone_events WHERE policy_key = 'bat_career_hr_100'")
        row = cursor.fetchone()
        assert row[0] == target_id

        # Verify temporary player was removed
        cursor.execute("SELECT COUNT(*) FROM players WHERE id = ?", (temp_id,))
        assert cursor.fetchone()[0] == 0
