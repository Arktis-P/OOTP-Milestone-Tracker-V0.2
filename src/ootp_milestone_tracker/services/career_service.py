import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..db.database import Database
from ..milestones.career_rules import DEFAULT_CAREER_MILESTONE_SETTINGS, get_ladder_thresholds
from ..milestones.context_models import AchievementContext
from ..milestones.context_renderer import render_korean_context
from ..milestones.context_resolver import ContextResolver


class CareerService:
    def __init__(self, database: Database):
        self.database = database

    def get_career_settings(self) -> Dict:
        with self.database.connect() as conn:
            rows = conn.execute("SELECT * FROM career_milestone_rule_settings").fetchall()
            if not rows:
                self.save_career_settings(DEFAULT_CAREER_MILESTONE_SETTINGS)
                return DEFAULT_CAREER_MILESTONE_SETTINGS

            settings = {}
            for r in rows:
                key = r["family_key"]
                enabled = bool(r["enabled"])
                try:
                    thresholds = json.loads(r["thresholds_json"])
                except Exception:
                    thresholds = DEFAULT_CAREER_MILESTONE_SETTINGS.get(key, {})
                settings[key] = thresholds

            for key, default_val in DEFAULT_CAREER_MILESTONE_SETTINGS.items():
                if key not in settings:
                    settings[key] = default_val

            return settings

    def save_career_settings(self, settings: Dict):
        with self.database.connect() as conn:
            for key, cfg in settings.items():
                conn.execute(
                    """INSERT INTO career_milestone_rule_settings (family_key, enabled, thresholds_json)
                    VALUES (?, 1, ?)
                    ON CONFLICT(family_key) DO UPDATE SET thresholds_json=excluded.thresholds_json""",
                    (key, json.dumps(cfg)),
                )
            conn.commit()

    def get_career_totals(self, player_id: int, competition_type: str = "regular_season") -> Dict:
        """Compute career totals combining latest career_checkpoint + game ledger deltas."""
        with self.database.connect() as conn:
            # 1. Get latest checkpoint
            cp = conn.execute(
                """SELECT * FROM career_checkpoints
                WHERE player_id = ? AND competition_type = ?
                ORDER BY season DESC, id DESC LIMIT 1""",
                (player_id, competition_type),
            ).fetchone()

            cutoff_game = cp["represented_game_cutoff"] if cp and cp["represented_game_cutoff"] else 0
            b_base = json.loads(cp["batting_json"]) if cp and cp["batting_json"] else {}
            p_base = json.loads(cp["pitching_json"]) if cp and cp["pitching_json"] else {}

            # 2. Get post-checkpoint game deltas
            b_rows = conn.execute(
                """SELECT b.* FROM player_game_batting b
                JOIN games g ON g.game_id = b.game_id
                WHERE b.player_id = ? AND g.competition_type = ? AND g.game_id > ?""",
                (player_id, competition_type, cutoff_game),
            ).fetchall()

            p_rows = conn.execute(
                """SELECT p.* FROM player_game_pitching p
                JOIN games g ON g.game_id = p.game_id
                WHERE p.player_id = ? AND g.competition_type = ? AND g.game_id > ?""",
                (player_id, competition_type, cutoff_game),
            ).fetchall()

            tot = {
                "g_batter": b_base.get("g", 0) + len(b_rows),
                "h": b_base.get("h", 0) + sum(r["h"] for r in b_rows),
                "hr": b_base.get("hr", 0) + sum(r["hr"] for r in b_rows),
                "r": b_base.get("r", 0) + sum(r["r"] for r in b_rows),
                "rbi": b_base.get("rbi", 0) + sum(r["rbi"] for r in b_rows),
                "sb": b_base.get("sb", 0) + sum(r["sb"] for r in b_rows),
                "bb": b_base.get("bb", 0) + sum(r["bb"] for r in b_rows),
                "g_pitcher": p_base.get("g", 0) + len(p_rows),
                "gs_pitcher": p_base.get("gs", 0) + sum(1 for r in p_rows if r["outs"] >= 15),
                "outs": p_base.get("outs", 0) + sum(r["outs"] for r in p_rows),
                "so": p_base.get("so", 0) + sum(r["so"] for r in p_rows),
                "w": p_base.get("w", 0) + sum(r["win"] for r in p_rows),
                "holds": p_base.get("holds", 0) + sum(r["hold"] for r in p_rows),
                "sv": p_base.get("sv", 0) + sum(r["save"] for r in p_rows),
            }
            tot["ip"] = tot["outs"] / 3.0
            return tot

    def rebuild_career_milestones(self, player_id: Optional[int] = None, competition_type: str = "regular_season"):
        """Rebuild career milestones and update targets chronologically."""
        settings = self.get_career_settings()
        with self.database.connect() as conn:
            # Clear existing game_crossing career achievements for targeted players
            if player_id:
                pids = [player_id]
                conn.execute("DELETE FROM career_milestone_achievements WHERE entity_id = ? AND competition_type = ?", (player_id, competition_type))
            else:
                p_rows = conn.execute("SELECT DISTINCT player_id FROM player_game_batting UNION SELECT DISTINCT player_id FROM player_game_pitching").fetchall()
                pids = [r["player_id"] for r in p_rows]
                conn.execute("DELETE FROM career_milestone_achievements WHERE competition_type = ?", (competition_type,))

            rule_titles = {
                "CAREER_G_BATTER": "통산 {}경기 출장",
                "CAREER_HITS": "통산 {}안타",
                "CAREER_HR": "통산 {}홈런",
                "CAREER_RUNS": "통산 {}득점",
                "CAREER_RBI": "통산 {}타점",
                "CAREER_SB": "통산 {}도루",
                "CAREER_BB": "통산 {}볼넷",
                "CAREER_G_PITCHER": "통산 {}경기 출장",
                "CAREER_GS_PITCHER": "통산 {}경기 선발",
                "CAREER_IP": "통산 {}이닝",
                "CAREER_STRIKEOUTS": "통산 {}탈삼진",
                "CAREER_WINS": "통산 {}승",
                "CAREER_HOLDS": "통산 {}홀드",
                "CAREER_SAVES": "통산 {}세이브",
            }

            for pid in pids:
                totals = self.get_career_totals(pid, competition_type)

                # Get games sorted chronologically
                b_games = conn.execute(
                    """SELECT b.*, g.game_date FROM player_game_batting b
                    JOIN games g ON g.game_id = b.game_id
                    WHERE b.player_id = ? AND g.competition_type = ?
                    ORDER BY g.game_date ASC, g.game_id ASC""",
                    (pid, competition_type),
                ).fetchall()

                p_games = conn.execute(
                    """SELECT p.*, g.game_date FROM player_game_pitching p
                    JOIN games g ON g.game_id = p.game_id
                    WHERE p.player_id = ? AND g.competition_type = ?
                    ORDER BY g.game_date ASC, g.game_id ASC""",
                    (pid, competition_type),
                ).fetchall()

                # Evaluate Batter Career Threshold Crossings
                b_cum = {"g_batter": 0, "h": 0, "hr": 0, "r": 0, "rbi": 0, "sb": 0, "bb": 0}
                for bg in b_games:
                    gid, gdate = bg["game_id"], bg["game_date"]
                    prev = dict(b_cum)
                    b_cum["g_batter"] += 1
                    b_cum["h"] += bg["h"]
                    b_cum["hr"] += bg["hr"]
                    b_cum["r"] += bg["r"]
                    b_cum["rbi"] += bg["rbi"]
                    b_cum["sb"] += bg["sb"]
                    b_cum["bb"] += bg["bb"]

                    for rkey, stat_name in [
                        ("CAREER_G_BATTER", "g_batter"),
                        ("CAREER_HITS", "h"),
                        ("CAREER_HR", "hr"),
                        ("CAREER_RUNS", "r"),
                        ("CAREER_RBI", "rbi"),
                        ("CAREER_SB", "sb"),
                        ("CAREER_BB", "bb"),
                    ]:
                        cfg = settings.get(rkey, DEFAULT_CAREER_MILESTONE_SETTINGS.get(rkey, {}))
                        thresholds = get_ladder_thresholds(cfg, b_cum[stat_name])
                        for t in thresholds:
                            if prev[stat_name] < t <= b_cum[stat_name]:
                                title = rule_titles[rkey].format(int(t))
                                conn.execute(
                                    """INSERT OR IGNORE INTO career_milestone_achievements
                                    (entity_type, entity_id, competition_type, rule_key, title, threshold_value, achieved_value, achieved_game_id, achieved_date, source)
                                    VALUES ('player', ?, ?, ?, ?, ?, ?, ?, ?, 'game_crossing')""",
                                    (pid, competition_type, f"{rkey}_{int(t)}", title, t, float(b_cum[stat_name]), gid, gdate),
                                )

                # Evaluate Pitcher Career Threshold Crossings
                p_cum = {"g_pitcher": 0, "gs_pitcher": 0, "outs": 0, "so": 0, "w": 0, "holds": 0, "sv": 0}
                for pg in p_games:
                    gid, gdate = pg["game_id"], pg["game_date"]
                    prev = dict(p_cum)
                    p_cum["g_pitcher"] += 1
                    if pg["outs"] >= 15:
                        p_cum["gs_pitcher"] += 1
                    p_cum["outs"] += pg["outs"]
                    p_cum["so"] += pg["so"]
                    p_cum["w"] += pg["win"]
                    p_cum["holds"] += pg["hold"]
                    p_cum["sv"] += pg["save"]

                    # Pitching Count Rules
                    for rkey, stat_name in [
                        ("CAREER_G_PITCHER", "g_pitcher"),
                        ("CAREER_GS_PITCHER", "gs_pitcher"),
                        ("CAREER_STRIKEOUTS", "so"),
                        ("CAREER_WINS", "w"),
                        ("CAREER_HOLDS", "holds"),
                        ("CAREER_SAVES", "sv"),
                    ]:
                        cfg = settings.get(rkey, DEFAULT_CAREER_MILESTONE_SETTINGS.get(rkey, {}))
                        thresholds = get_ladder_thresholds(cfg, p_cum[stat_name])
                        for t in thresholds:
                            if prev[stat_name] < t <= p_cum[stat_name]:
                                title = rule_titles[rkey].format(int(t))
                                conn.execute(
                                    """INSERT OR IGNORE INTO career_milestone_achievements
                                    (entity_type, entity_id, competition_type, rule_key, title, threshold_value, achieved_value, achieved_game_id, achieved_date, source)
                                    VALUES ('player', ?, ?, ?, ?, ?, ?, ?, ?, 'game_crossing')""",
                                    (pid, competition_type, f"{rkey}_{int(t)}", title, t, float(p_cum[stat_name]), gid, gdate),
                                )

                    # CAREER_IP (evaluated in outs)
                    ip_cfg = settings.get("CAREER_IP", DEFAULT_CAREER_MILESTONE_SETTINGS["CAREER_IP"])
                    ip_thresholds = get_ladder_thresholds(ip_cfg, p_cum["outs"] / 3.0)
                    for ip_t in ip_thresholds:
                        t_outs = ip_t * 3
                        if prev["outs"] < t_outs <= p_cum["outs"]:
                            title = f"통산 {int(ip_t)}이닝"
                            conn.execute(
                                """INSERT OR IGNORE INTO career_milestone_achievements
                                (entity_type, entity_id, competition_type, rule_key, title, threshold_value, achieved_value, achieved_game_id, achieved_date, source)
                                VALUES ('player', ?, ?, ?, ?, ?, ?, ?, ?, 'game_crossing')""",
                                (pid, competition_type, f"CAREER_IP_{int(ip_t)}", title, ip_t, p_cum["outs"] / 3.0, gid, gdate),
                            )

                # Update milestones table target tracker for UI
                self._update_milestone_targets(conn, pid, totals, settings)

            conn.commit()

    def _update_milestone_targets(self, conn, pid: int, totals: Dict, settings: Dict):
        """Update milestones table rows for player career targets."""
        targets = [
            ("H", "Career Hits", totals["h"], settings.get("CAREER_HITS", {})),
            ("HR", "Career Home Runs", totals["hr"], settings.get("CAREER_HR", {})),
            ("RBI", "Career RBI", totals["rbi"], settings.get("CAREER_RBI", {})),
            ("W", "Career Wins", totals["w"], settings.get("CAREER_WINS", {})),
            ("SO", "Career Strikeouts", totals["so"], settings.get("CAREER_STRIKEOUTS", {})),
            ("IP", "Career Innings", totals["ip"], settings.get("CAREER_IP", {})),
        ]
        for stat_key, label_prefix, curr_val, cfg in targets:
            ladder = get_ladder_thresholds(cfg, curr_val)
            if not ladder:
                continue
            # Find next target > curr_val or highest achieved
            target_val = next((t for t in sorted(ladder) if t > curr_val), ladder[-1])
            achieved = 1 if curr_val >= target_val else 0
            label = f"{target_val:,.0f} {label_prefix}"

            conn.execute(
                """INSERT INTO milestones (entity_type, entity_id, scope, stat_key, label, current_value, target_value, achieved, sort_order)
                VALUES ('player', ?, 'career', ?, ?, ?, ?, ?, 10)
                ON CONFLICT DO UPDATE SET current_value=excluded.current_value, target_value=excluded.target_value, achieved=excluded.achieved""",
                (pid, stat_key, label, curr_val, target_val, achieved),
            )
