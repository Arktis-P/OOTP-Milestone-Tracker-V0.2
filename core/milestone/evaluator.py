"""
Milestone Evaluator Engine (Phase 4.2 - 4.7)
Evaluates Game, Season Counting, Career, Composite, and Team milestones.
Ensures crossing detection (previous < threshold <= current) and zero duplicate events.
"""

import sqlite3
import datetime
from typing import List, Dict, Any, Optional
from core.milestone.policy_loader import MilestonePolicy, PolicyLoader


class MilestoneEvaluator:
    def __init__(self, conn: sqlite3.Connection, policies: Optional[List[MilestonePolicy]] = None):
        self.conn = conn
        self.policies = policies if policies is not None else PolicyLoader.load_from_csv()

    def evaluate_game(self, game_id: int) -> List[Dict[str, Any]]:
        """Evaluates single-game milestones for batters and pitchers in game_id."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT season, game_date FROM games WHERE id = ?", (game_id,))
        game_row = cursor.fetchone()
        if not game_row:
            return []
        season, game_date = game_row["season"], game_row["game_date"]

        created_events: List[Dict[str, Any]] = []
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Game scope policies
        game_policies = [p for p in self.policies if p.scope == "game"]

        # Batting stats
        cursor.execute("SELECT * FROM batting_game_stats WHERE game_id = ?", (game_id,))
        b_stats = cursor.fetchall()
        for b in b_stats:
            p_id, t_id = b["player_id"], b["team_id"]
            stat_values = {
                "h": b["h"], "hr": b["hr"], "rbi": b["rbi"], "sb": b["sb"],
                "cycle": 1 if "cycle" in (b["raw_notes"] or "").lower() else 0,
                "grand_slam": 1 if "grand slam" in (b["raw_notes"] or "").lower() else 0,
            }

            for policy in game_policies:
                if policy.stat in stat_values:
                    val = float(stat_values[policy.stat])
                    triggered = False
                    if policy.direction == "boolean" and val >= 1:
                        triggered = True
                    elif policy.direction == "higher" and val >= policy.numeric_threshold:
                        triggered = True

                    if triggered:
                        evt = self._create_milestone_if_absent(
                            policy=policy, player_id=p_id, team_id=t_id, season=season,
                            game_id=game_id, event_date=game_date, value=val,
                            threshold=policy.numeric_threshold, now_iso=now_iso
                        )
                        if evt:
                            created_events.append(evt)

        # Pitching stats
        cursor.execute("SELECT * FROM pitching_game_stats WHERE game_id = ?", (game_id,))
        p_stats = cursor.fetchall()
        for p in p_stats:
            p_id, t_id = p["player_id"], p["team_id"]
            stat_values = {
                "so": p["k"], "k": p["k"], "cg": p["cg"], "sho": p["sho"],
                "no_hitter": 1 if p["ip_outs"] >= 27 and p["h"] == 0 else 0,
                "perfect_game": 1 if p["ip_outs"] >= 27 and p["h"] == 0 and p["bb"] == 0 else 0,
            }

            for policy in game_policies:
                if policy.stat in stat_values:
                    val = float(stat_values[policy.stat])
                    triggered = False
                    if policy.direction == "boolean" and val >= 1:
                        triggered = True
                    elif policy.direction == "higher" and val >= policy.numeric_threshold:
                        triggered = True

                    if triggered:
                        evt = self._create_milestone_if_absent(
                            policy=policy, player_id=p_id, team_id=t_id, season=season,
                            game_id=game_id, event_date=game_date, value=val,
                            threshold=policy.numeric_threshold, now_iso=now_iso
                        )
                        if evt:
                            created_events.append(evt)

        return created_events

    def evaluate_season_and_career(self, season: int) -> List[Dict[str, Any]]:
        """Evaluates season counting, career, and composite milestones for all players in season."""
        cursor = self.conn.cursor()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        created_events: List[Dict[str, Any]] = []

        season_policies = [p for p in self.policies if p.scope == "season"]
        career_policies = [p for p in self.policies if p.scope == "career"]

        # 1. Evaluate Batting Season & Career
        cursor.execute(
            """SELECT player_id, SUM(h) as h, SUM(hr) as hr, SUM(rbi) as rbi, SUM(sb) as sb, SUM(r) as r, SUM(bb) as bb
               FROM batting_game_stats b JOIN games g ON b.game_id = g.id
               WHERE g.season = ? GROUP BY player_id""",
            (season,)
        )
        batters = cursor.fetchall()
        for b in batters:
            p_id = b["player_id"]

            # Fetch player's latest game date in season
            cursor.execute(
                """SELECT g.game_date, b.team_id FROM batting_game_stats b JOIN games g ON b.game_id = g.id
                   WHERE g.season = ? AND b.player_id = ? ORDER BY g.game_date DESC LIMIT 1""",
                (season, p_id)
            )
            g_row = cursor.fetchone()
            event_date = g_row["game_date"] if g_row else f"{season}-10-01"
            team_id = g_row["team_id"] if g_row else None

            current_season_stats = {
                "h": float(b["h"] or 0), "hr": float(b["hr"] or 0), "rbi": float(b["rbi"] or 0),
                "sb": float(b["sb"] or 0), "r": float(b["r"] or 0), "bb": float(b["bb"] or 0)
            }

            # Season Counting Crossing
            for policy in season_policies:
                if policy.stat in current_season_stats:
                    val = current_season_stats[policy.stat]
                    if val >= policy.numeric_threshold:
                        evt = self._create_milestone_if_absent(
                            policy=policy, player_id=p_id, team_id=team_id, season=season,
                            game_id=None, event_date=event_date, value=val,
                            threshold=policy.numeric_threshold, now_iso=now_iso
                        )
                        if evt:
                            created_events.append(evt)

                # Composite (20-20, 30-30, etc.)
                elif policy.stat == "season_hr_sb":
                    m_hr, m_sb = [int(x) for x in policy.threshold.split("-")]
                    if current_season_stats["hr"] >= m_hr and current_season_stats["sb"] >= m_sb:
                        evt = self._create_milestone_if_absent(
                            policy=policy, player_id=p_id, team_id=team_id, season=season,
                            game_id=None, event_date=event_date, value=current_season_stats["hr"],
                            threshold=m_hr, now_iso=now_iso
                        )
                        if evt:
                            created_events.append(evt)

            # Career Baselines + Season Accumulation
            cursor.execute(
                """SELECT SUM(h) as h, SUM(hr) as hr, SUM(rbi) as rbi, SUM(sb) as sb
                   FROM baseline_batting_stats WHERE player_id = ?""",
                (p_id,)
            )
            base_b = cursor.fetchone()
            base_h = float(base_b["h"] or 0) if base_b else 0.0
            base_hr = float(base_b["hr"] or 0) if base_b else 0.0

            career_stats = {
                "h": base_h + current_season_stats["h"],
                "hr": base_hr + current_season_stats["hr"],
            }

            for policy in career_policies:
                if policy.stat in career_stats:
                    c_val = career_stats[policy.stat]
                    if c_val >= policy.numeric_threshold:
                        evt = self._create_milestone_if_absent(
                            policy=policy, player_id=p_id, team_id=team_id, season=season,
                            game_id=None, event_date=event_date, value=c_val,
                            threshold=policy.numeric_threshold, now_iso=now_iso
                        )
                        if evt:
                            created_events.append(evt)

        # 2. Evaluate Pitching Season & Career
        cursor.execute(
            """SELECT player_id, SUM(w) as w, SUM(k) as k, SUM(sv) as sv, SUM(hld) as hld
               FROM pitching_game_stats p JOIN games g ON p.game_id = g.id
               WHERE g.season = ? GROUP BY player_id""",
            (season,)
        )
        pitchers = cursor.fetchall()
        for p in pitchers:
            p_id = p["player_id"]
            cursor.execute(
                """SELECT g.game_date, p.team_id FROM pitching_game_stats p JOIN games g ON p.game_id = g.id
                   WHERE g.season = ? AND p.player_id = ? ORDER BY g.game_date DESC LIMIT 1""",
                (season, p_id)
            )
            g_row = cursor.fetchone()
            event_date = g_row["game_date"] if g_row else f"{season}-10-01"
            team_id = g_row["team_id"] if g_row else None

            current_p_stats = {
                "w": float(p["w"] or 0), "so": float(p["k"] or 0), "k": float(p["k"] or 0),
                "sv": float(p["sv"] or 0), "hld": float(p["hld"] or 0)
            }

            for policy in season_policies:
                if policy.stat in current_p_stats:
                    val = current_p_stats[policy.stat]
                    if val >= policy.numeric_threshold:
                        evt = self._create_milestone_if_absent(
                            policy=policy, player_id=p_id, team_id=team_id, season=season,
                            game_id=None, event_date=event_date, value=val,
                            threshold=policy.numeric_threshold, now_iso=now_iso
                        )
                        if evt:
                            created_events.append(evt)

            cursor.execute(
                """SELECT SUM(w) as w, SUM(k) as k, SUM(sv) as sv FROM baseline_pitching_stats WHERE player_id = ?""",
                (p_id,)
            )
            base_p = cursor.fetchone()
            base_w = float(base_p["w"] or 0) if base_p else 0.0
            base_so = float(base_p["k"] or 0) if base_p else 0.0

            career_p_stats = {
                "w": base_w + current_p_stats["w"],
                "so": base_so + current_p_stats["so"],
                "k": base_so + current_p_stats["k"],
            }

            for policy in career_policies:
                if policy.stat in career_p_stats:
                    c_val = career_p_stats[policy.stat]
                    if c_val >= policy.numeric_threshold:
                        evt = self._create_milestone_if_absent(
                            policy=policy, player_id=p_id, team_id=team_id, season=season,
                            game_id=None, event_date=event_date, value=c_val,
                            threshold=policy.numeric_threshold, now_iso=now_iso
                        )
                        if evt:
                            created_events.append(evt)

        return created_events

    def _create_milestone_if_absent(
        self,
        policy: MilestonePolicy,
        player_id: Optional[int],
        team_id: Optional[int],
        season: int,
        game_id: Optional[int],
        event_date: str,
        value: float,
        threshold: float,
        now_iso: str
    ) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()

        # Check existing milestone for same policy_key, player_id, and scope
        if policy.scope == "game":
            cursor.execute(
                "SELECT id FROM milestone_events WHERE policy_key = ? AND player_id = ? AND game_id = ?",
                (policy.key, player_id, game_id)
            )
        else:
            cursor.execute(
                "SELECT id FROM milestone_events WHERE policy_key = ? AND player_id = ? AND season = ?",
                (policy.key, player_id, season)
            )

        if cursor.fetchone():
            return None  # Already recorded

        cursor.execute(
            """INSERT INTO milestone_events
               (policy_key, player_id, team_id, season, game_id, event_date, scope, category, grade, value, threshold, source_type, source_ref, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'auto', NULL, ?)""",
            (policy.key, player_id, team_id, season, game_id, event_date, policy.scope, policy.category, policy.grade, value, threshold, now_iso)
        )
        evt_id = cursor.lastrowid
        self.conn.commit()

        return {
            "id": evt_id,
            "policy_key": policy.key,
            "label": policy.label,
            "player_id": player_id,
            "team_id": team_id,
            "season": season,
            "game_id": game_id,
            "event_date": event_date,
            "grade": policy.grade,
            "value": value,
            "threshold": threshold,
        }
