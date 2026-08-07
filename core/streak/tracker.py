"""
Streak Tracker Engine (Phase 7.1, 7.2)
Tracks active hitting, home run, and team win streaks per boxscore import in date order.
"""

import os
import json
import sqlite3
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

DEFAULT_STREAK_POLICY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "streak_policies.json")


@dataclass
class StreakPolicy:
    key: str
    label: str
    subject: str  # player or team
    category: str
    stat: str
    continue_when: Optional[Dict[str, Any]] = None
    minimum_to_record: int = 5
    scope: str = "season"


class StreakTracker:
    def __init__(self, conn: sqlite3.Connection, policy_path: str = DEFAULT_STREAK_POLICY_PATH):
        self.conn = conn
        self.policies = self.load_policies(policy_path)

    @staticmethod
    def load_policies(json_path: str) -> List[StreakPolicy]:
        if not os.path.exists(json_path):
            return []
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [StreakPolicy(**item) for item in data]

    def update_streaks_for_game(self, game_id: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT season, game_date, home_team_id, away_team_id FROM games WHERE id = ?", (game_id,))
        game_row = cursor.fetchone()
        if not game_row:
            return
        season, game_date = game_row["season"], game_row["game_date"]

        for policy in self.policies:
            if policy.subject == "player":
                # Process Player Batting Streaks
                cursor.execute("SELECT player_id, h, hr FROM batting_game_stats WHERE game_id = ?", (game_id,))
                b_lines = cursor.fetchall()
                for b in b_lines:
                    p_id = b["player_id"]
                    val = b["h"] if policy.stat == "h" else b["hr"]
                    self._update_subject_streak(policy, "player", p_id, season, game_date, val >= 1)

    def _update_subject_streak(
        self,
        policy: StreakPolicy,
        subject_type: str,
        subject_id: int,
        season: int,
        game_date: str,
        condition_met: bool
    ) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT start_date, last_date, current_value FROM streak_states
               WHERE policy_key = ? AND subject_type = ? AND subject_id = ? AND season = ?""",
            (policy.key, subject_type, subject_id, season)
        )
        state = cursor.fetchone()

        if condition_met:
            if not state:
                # Start new streak
                cursor.execute(
                    """INSERT INTO streak_states (policy_key, subject_type, subject_id, season, start_date, last_date, current_value)
                       VALUES (?, ?, ?, ?, ?, ?, 1)""",
                    (policy.key, subject_type, subject_id, season, game_date, game_date)
                )
            else:
                curr_val = state["current_value"] + 1
                cursor.execute(
                    """UPDATE streak_states SET last_date = ?, current_value = ?
                       WHERE policy_key = ? AND subject_type = ? AND subject_id = ? AND season = ?""",
                    (game_date, curr_val, policy.key, subject_type, subject_id, season)
                )
        else:
            if state:
                # Streak ended
                start_date = state["start_date"]
                final_val = state["current_value"]

                if final_val >= policy.minimum_to_record:
                    cursor.execute(
                        """INSERT INTO streak_events (policy_key, subject_type, subject_id, season, start_date, end_date, final_value)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (policy.key, subject_type, subject_id, season, start_date, game_date, final_val)
                    )

                cursor.execute(
                    """DELETE FROM streak_states
                       WHERE policy_key = ? AND subject_type = ? AND subject_id = ? AND season = ?""",
                    (policy.key, subject_type, subject_id, season)
                )
        self.conn.commit()
