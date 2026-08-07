"""
Unit tests for Import Pipeline & Idempotency (Phase 3)
"""

import os
import shutil
import tempfile
import time
import pytest
from core.db.connection import DatabaseManager
from core.import_workflow.baseline_import import BaselineImportService
from core.import_workflow.boxscore_import import BoxscoreImportService
from core.import_workflow.auto_watcher import LiveAutoWatcher

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def temp_db(tmp_path):
    db_path = str(tmp_path / "test_import.db")
    db_mgr = DatabaseManager(db_path)
    db_mgr.initialize_database()
    return db_mgr


def test_baseline_import_and_idempotency(temp_db):
    bat_file = os.path.join(FIXTURES_DIR, "player_batting_stats_sample.txt")
    pitch_file = os.path.join(FIXTURES_DIR, "player_pitching_stats_sample.txt")

    if not os.path.exists(bat_file) or not os.path.exists(pitch_file):
        pytest.skip("Baseline sample files missing.")

    with temp_db.get_connection() as conn:
        svc = BaselineImportService(conn)
        res1 = svc.import_baselines(bat_file, pitch_file, season=2026, mode="first_time")

        assert res1["status"] == "success"
        assert res1["batting_records_imported"] > 0
        assert res1["pitching_records_imported"] > 0

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM baseline_batting_stats WHERE season = 2026")
        count_first = cursor.fetchone()[0]
        assert count_first > 0

        # Refresh import should replace, not double count
        res2 = svc.import_baselines(bat_file, pitch_file, season=2026, mode="refresh")
        cursor.execute("SELECT COUNT(*) FROM baseline_batting_stats WHERE season = 2026")
        count_refresh = cursor.fetchone()[0]

        assert count_refresh == count_first


def test_boxscore_import_idempotency_and_modified(temp_db):
    box_path = os.path.join(FIXTURES_DIR, "game_box_1.html")
    if not os.path.exists(box_path):
        pytest.skip("game_box_1.html missing.")

    with temp_db.get_connection() as conn:
        svc = BoxscoreImportService(conn)

        # First import
        res1 = svc.import_boxscore(box_path)
        assert res1["status"] == "success"

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM batting_game_stats")
        bat_count1 = cursor.fetchone()[0]
        assert bat_count1 > 0

        # Second import (unchanged)
        res2 = svc.import_boxscore(box_path)
        assert res2["status"] == "unchanged"

        cursor.execute("SELECT COUNT(*) FROM batting_game_stats")
        bat_count2 = cursor.fetchone()[0]
        assert bat_count2 == bat_count1  # No duplicate rows created!


def test_boxscore_dir_batch_import(temp_db):
    with temp_db.get_connection() as conn:
        svc = BoxscoreImportService(conn)
        res = svc.import_boxscores_dir(FIXTURES_DIR)

        assert res["total_found"] >= 4
        assert res["imported"] >= 1
        assert res["errors_count"] == 0


def test_live_auto_watcher(temp_db, tmp_path):
    # Create temp boxscores directory
    box_dir = str(tmp_path / "box_scores")
    os.makedirs(box_dir, exist_ok=True)

    imported_events = []
    watcher = LiveAutoWatcher(
        boxscores_dir=box_dir,
        db_path=temp_db.db_path,
        on_import_callback=lambda event: imported_events.append(event),
        poll_interval=0.2
    )

    watcher.start()
    assert watcher.is_running()

    # Copy sample game_box_1.html into box_dir
    src_box = os.path.join(FIXTURES_DIR, "game_box_1.html")
    dest_box = os.path.join(box_dir, "game_box_1.html")
    shutil.copy(src_box, dest_box)

    # Wait for watcher poll
    time.sleep(0.8)
    watcher.stop()

    assert len(imported_events) >= 1
    assert imported_events[0]["status"] == "success"
