"""
Unit tests for Milestone Policy Engine & Crossing Detection (Phase 4)
"""

import os
import shutil
import tempfile
import pytest
from core.db.connection import DatabaseManager
from core.milestone.policy_loader import PolicyLoader
from core.milestone.evaluator import MilestoneEvaluator
from core.import_workflow.boxscore_import import BoxscoreImportService

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def temp_db(tmp_path):
    db_path = str(tmp_path / "test_milestone.db")
    db_mgr = DatabaseManager(db_path)
    db_mgr.initialize_database()
    return db_mgr


def test_policy_loader():
    policies = PolicyLoader.load_from_csv()
    assert len(policies) > 0
    keys = {p.key for p in policies}
    assert "bat_game_hr_3" in keys
    assert "bat_season_hr_30" in keys
    assert "bat_career_h_3000" in keys
    assert "bat_season_composite_30_30" in keys


def test_game_milestone_evaluation(temp_db):
    box_path = os.path.join(FIXTURES_DIR, "game_box_1.html")
    if not os.path.exists(box_path):
        pytest.skip("game_box_1.html missing.")

    with temp_db.get_connection() as conn:
        box_svc = BoxscoreImportService(conn)
        res = box_svc.import_boxscore(box_path)
        game_id = res["game_id"]

        evaluator = MilestoneEvaluator(conn)
        events = evaluator.evaluate_game(game_id)
        assert isinstance(events, list)

        # Ensure no duplicates when evaluated again
        events_dup = evaluator.evaluate_game(game_id)
        assert len(events_dup) == 0


def test_season_and_career_milestone_evaluation(temp_db):
    with temp_db.get_connection() as conn:
        conn.execute("INSERT INTO teams (id, team_key, name) VALUES (1, 'team_1', 'Team One')")
        # Insert test player with 35 HRs (triggers season 30 HR) and 20-20 stats
        conn.execute(
            "INSERT INTO players (id, ootp_player_id, first_name, last_name, display_name, is_temporary) VALUES (1, 8888, 'Power', 'Hitter', 'Power Hitter', 0)"
        )
        conn.execute(
            "INSERT INTO games (id, season, ootp_game_id, game_date) VALUES (10, 2026, 10, '2026-08-01')"
        )
        conn.execute(
            """INSERT INTO batting_game_stats (game_id, player_id, team_id, ab, r, h, hr, rbi, sb)
               VALUES (10, 1, 1, 100, 40, 50, 35, 90, 25)"""
        )
        conn.commit()

        evaluator = MilestoneEvaluator(conn)
        events = evaluator.evaluate_season_and_career(2026)

        keys = {e["policy_key"] for e in events}
        assert "bat_season_hr_30" in keys
        assert "bat_season_composite_20_20" in keys
        assert "bat_career_first_h" in keys  # 0 -> 1 first hit

        # Re-evaluate to verify idempotency
        events_again = evaluator.evaluate_season_and_career(2026)
        assert len(events_again) == 0
