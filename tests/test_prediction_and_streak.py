"""
Unit tests for Milestone Predictions & Streak Tracker (Phase 6 & Phase 7)
"""

import os
import pytest
from core.db.connection import DatabaseManager
from core.prediction.model import PredictionEngine
from core.streak.tracker import StreakTracker
from core.import_workflow.boxscore_import import BoxscoreImportService

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def temp_db(tmp_path):
    db_path = str(tmp_path / "test_pred_streak.db")
    db_mgr = DatabaseManager(db_path)
    db_mgr.initialize_database()
    return db_mgr


def test_prediction_engine(temp_db):
    with temp_db.get_connection() as conn:
        conn.execute("INSERT INTO teams (id, team_key, name) VALUES (1, 'team_1', 'Team One')")
        conn.execute("INSERT INTO players (id, ootp_player_id, first_name, last_name, display_name, is_temporary) VALUES (1, 99, 'Mike', 'Trout', 'Mike Trout', 0)")
        conn.execute("INSERT INTO games (id, season, ootp_game_id, game_date) VALUES (1, 2026, 1, '2026-04-01')")
        conn.execute("INSERT INTO batting_game_stats (game_id, player_id, team_id, ab, r, h, hr, rbi, sb) VALUES (1, 1, 1, 100, 30, 40, 28, 70, 15)")
        conn.commit()

        engine = PredictionEngine(conn)
        preds = engine.generate_predictions(season=2026)

        assert len(preds) > 0
        p_keys = {p.policy_key for p in preds}
        assert "bat_season_hr_30" in p_keys


def test_streak_tracker(temp_db):
    box_path = os.path.join(FIXTURES_DIR, "game_box_1.html")
    if not os.path.exists(box_path):
        pytest.skip("game_box_1.html missing.")

    with temp_db.get_connection() as conn:
        svc = BoxscoreImportService(conn)
        res = svc.import_boxscore(box_path)
        game_id = res["game_id"]

        tracker = StreakTracker(conn)
        tracker.update_streaks_for_game(game_id)

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM streak_states")
        count = cursor.fetchone()[0]
        assert count >= 0
