"""
End-to-End (E2E) Full System Integration Test (Phase 16.1)
Simulates complete user journey:
Save Configuration -> Baseline Import -> Boxscore Import -> Milestone Evaluation ->
Prediction Generation -> Streak Tracking -> Manual Event -> Season Isolation Validation Replay.
"""

import os
import shutil
import tempfile
import pytest
from core.config.settings import Settings, SettingsManager
from core.db.connection import DatabaseManager
from core.import_workflow.baseline_import import BaselineImportService
from core.import_workflow.boxscore_import import BoxscoreImportService
from core.milestone.evaluator import MilestoneEvaluator
from core.prediction.model import PredictionEngine
from core.streak.tracker import StreakTracker
from core.db.manual_event_repo import ManualEventRepository
from core.validation.season_validator import SeasonValidator

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_full_e2e_user_journey(tmp_path):
    config_dir = str(tmp_path / "config")
    mgr = SettingsManager(config_dir=config_dir)

    # 1. Save Settings
    settings = Settings(
        active_save_path=str(tmp_path / "DummySave.lg"),
        current_season=2027,
    )
    mgr.save(settings)

    readiness = mgr.check_readiness(settings)
    db_path = readiness["db_path"]

    db_mgr = DatabaseManager(db_path, save_key=settings.save_key)
    db_mgr.initialize_database()

    with db_mgr.get_connection() as conn:
        # 2. Baseline Stats Import
        bat_txt = os.path.join(FIXTURES_DIR, "player_batting_stats_sample.txt")
        pitch_txt = os.path.join(FIXTURES_DIR, "player_pitching_stats_sample.txt")

        if os.path.exists(bat_txt) and os.path.exists(pitch_txt):
            b_svc = BaselineImportService(conn)
            b_res = b_svc.import_baselines(bat_txt, pitch_txt, season=2027, mode="first_time")
            assert b_res["status"] == "success"

        # 3. Boxscores Import
        box_svc = BoxscoreImportService(conn)
        box_res = box_svc.import_boxscores_dir(FIXTURES_DIR)
        assert box_res["imported"] >= 1

        # 4. Milestone Evaluation
        evaluator = MilestoneEvaluator(conn)
        game_events = evaluator.evaluate_game(1)
        season_events = evaluator.evaluate_season_and_career(2027)

        # 5. Prediction Engine
        pred_engine = PredictionEngine(conn)
        preds = pred_engine.generate_predictions(2027)
        assert isinstance(preds, list)

        # 6. Streak Tracker
        tracker = StreakTracker(conn)
        tracker.update_streaks_for_game(1)

        # 7. Manual Event Registration
        manual_repo = ManualEventRepository(conn)
        m_res = manual_repo.add_manual_event(
            event_type="award",
            first_name="Test",
            last_name="Hero",
            season=2027,
            event_date="2027-10-15",
            title="E2E Special Award"
        )
        assert m_res["id"] > 0

    # 8. Season Isolation Replay Validation
    validator = SeasonValidator(
        operating_db_path=db_path,
        boxscores_dir=FIXTURES_DIR,
        import_export_dir=FIXTURES_DIR
    )
    val_res = validator.validate_season(2027)
    assert val_res["operating_game_count"] >= 1
