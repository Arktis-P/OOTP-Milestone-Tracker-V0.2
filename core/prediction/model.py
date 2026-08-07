"""
Milestone Prediction Model Engine (Phase 6.1)
Projects season pace, career milestone proximity, and remaining goals based on track_from and near_n policies.
"""

import sqlite3
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from core.milestone.policy_loader import MilestonePolicy, PolicyLoader


@dataclass
class PredictionResult:
    policy_key: str
    label: str
    player_id: Optional[int]
    player_name: str
    category: str
    stat: str
    current_value: float
    target: float
    remaining: float
    season_pace: float
    projected_final: float
    is_near: bool
    explanation: str


class PredictionEngine:
    TOTAL_SEASON_GAMES = 162

    def __init__(self, conn: sqlite3.Connection, policies: Optional[List[MilestonePolicy]] = None):
        self.conn = conn
        self.policies = policies if policies is not None else PolicyLoader.load_from_csv()

    def generate_predictions(self, season: int) -> List[PredictionResult]:
        cursor = self.conn.cursor()
        results: List[PredictionResult] = []

        # Count total games played in season
        cursor.execute("SELECT COUNT(DISTINCT id) FROM games WHERE season = ?", (season,))
        total_games_played = cursor.fetchone()[0] or 1
        games_played = max(1, min(total_games_played, self.TOTAL_SEASON_GAMES))

        # Filter policies with track_from or numeric threshold
        pred_policies = [p for p in self.policies if p.scope in ("season", "career") and p.direction == "higher"]

        # Batters
        cursor.execute(
            """SELECT b.player_id, p.display_name, SUM(b.h) as h, SUM(b.hr) as hr, SUM(b.rbi) as rbi, SUM(b.sb) as sb
               FROM batting_game_stats b JOIN games g ON b.game_id = g.id JOIN players p ON b.player_id = p.id
               WHERE g.season = ? GROUP BY b.player_id""",
            (season,)
        )
        batters = cursor.fetchall()

        for b in batters:
            p_id = b["player_id"]
            p_name = b["display_name"]
            stats = {"h": float(b["h"]), "hr": float(b["hr"]), "rbi": float(b["rbi"]), "sb": float(b["sb"])}

            for policy in pred_policies:
                if policy.stat in stats:
                    curr_val = stats[policy.stat]
                    target = policy.numeric_threshold

                    # Check track_from requirement
                    if policy.track_from is not None and curr_val < policy.track_from:
                        continue

                    if curr_val >= target:
                        continue  # Already achieved

                    remaining = target - curr_val
                    pace_per_game = curr_val / games_played
                    projected_additional = pace_per_game * (self.TOTAL_SEASON_GAMES - games_played)
                    projected_final = curr_val + projected_additional

                    is_near = (policy.near_n is not None and remaining <= policy.near_n)
                    expl = f"현재 {games_played}경기 기준 경기당 {pace_per_game:.2f}개 페이스 (예상 최종: {projected_final:.1f})"

                    results.append(
                        PredictionResult(
                            policy_key=policy.key,
                            label=policy.label,
                            player_id=p_id,
                            player_name=p_name,
                            category=policy.category,
                            stat=policy.stat,
                            current_value=curr_val,
                            target=target,
                            remaining=remaining,
                            season_pace=round(pace_per_game, 3),
                            projected_final=round(projected_final, 1),
                            is_near=is_near,
                            explanation=expl,
                        )
                    )

        return sorted(results, key=lambda r: (not r.is_near, r.remaining))
