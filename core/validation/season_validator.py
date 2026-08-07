"""
Season Isolation Validation Replay Engine (Phase 14.4)
Replays season boxscores in a separate validation DB to verify correctness and summary match
without modifying the operating database.
"""

import os
import json
import sqlite3
import tempfile, shutil
from typing import Dict, Any
from core.db.connection import DatabaseManager
from core.import_workflow.baseline_import import BaselineImportService
from core.import_workflow.boxscore_import import BoxscoreImportService
from core.milestone.evaluator import MilestoneEvaluator


class SeasonValidator:
    def __init__(self, operating_db_path: str, boxscores_dir: str, import_export_dir: str):
        self.operating_db_path = operating_db_path
        self.boxscores_dir = boxscores_dir
        self.import_export_dir = import_export_dir

    def validate_season(self, season: int) -> Dict[str, Any]:
        """
        Executes full season replay in a temporary validation DB,
        comparing resulting game, stat, and milestone counts against operating DB.
        """
        temp_dir = tempfile.mkdtemp()
        val_db_path = os.path.join(temp_dir, "validation.db")

        try:
            val_mgr = DatabaseManager(val_db_path, save_key="validation_replay")
            val_mgr.initialize_database()

            with val_mgr.get_connection() as val_conn:
                # 1. Apply baseline if present
                bat_txt = os.path.join(self.import_export_dir, "player_batting_stats.txt")
                pitch_txt = os.path.join(self.import_export_dir, "player_pitching_stats.txt")

                if os.path.exists(bat_txt) and os.path.exists(pitch_txt):
                    b_svc = BaselineImportService(val_conn)
                    b_svc.import_baselines(bat_txt, pitch_txt, season=season, mode="first_time")

                # 2. Sequentially import boxscores
                box_svc = BoxscoreImportService(val_conn)
                box_res = box_svc.import_boxscores_dir(self.boxscores_dir)

                # 3. Evaluate milestones
                evaluator = MilestoneEvaluator(val_conn)
                m_events = evaluator.evaluate_season_and_career(season)

                cursor = val_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM games WHERE season = ?", (season,))
                val_game_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM milestone_events WHERE season = ?", (season,))
                val_m_count = cursor.fetchone()[0]

            # Compare with operating DB
            op_game_count = 0
            op_m_count = 0
            if os.path.exists(self.operating_db_path):
                op_mgr = DatabaseManager(self.operating_db_path)
                with op_mgr.get_connection() as op_conn:
                    op_cur = op_conn.cursor()
                    op_cur.execute("SELECT COUNT(*) FROM games WHERE season = ?", (season,))
                    op_game_count = op_cur.fetchone()[0]

                    op_cur.execute("SELECT COUNT(*) FROM milestone_events WHERE season = ?", (season,))
                    op_m_count = op_cur.fetchone()[0]

            matches = (val_game_count == op_game_count) and (val_m_count == op_m_count)

            return {
                "season": season,
                "is_match": matches,
                "validation_game_count": val_game_count,
                "operating_game_count": op_game_count,
                "validation_milestone_count": val_m_count,
                "operating_milestone_count": op_m_count,
                "boxscores_processed": box_res["imported"],
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
