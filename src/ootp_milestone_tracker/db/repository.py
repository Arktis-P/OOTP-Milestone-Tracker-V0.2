import json
from typing import Dict, List, Optional

from ..importer.game_models import BattingEvent, BattingLine, GameRecord, PitchingLine
from ..milestones.game_evaluator import DEFAULT_GAME_MILESTONE_SETTINGS, GameMilestoneEvaluator


class Repository:
    def __init__(self, database):
        self.database = database

    def _all(self, sql, params=()):
        with self.database.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def _one(self, sql, params=()):
        with self.database.connect() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def teams(self):
        return self._all("SELECT * FROM teams ORDER BY is_tracked DESC, name")

    def tracked_team(self):
        return self._one("SELECT * FROM teams WHERE is_tracked = 1 LIMIT 1")

    def set_tracked_team(self, team_id: int):
        with self.database.connect() as conn:
            conn.execute("UPDATE teams SET is_tracked = 0")
            conn.execute("UPDATE teams SET is_tracked = 1 WHERE id = ?", (team_id,))
            conn.commit()

    def players(self, search: str = ""):
        like = f"%{search.strip()}%"
        return self._all(
            """SELECT p.*, t.name AS team_name, t.short_name, t.is_tracked
            FROM players p JOIN teams t ON t.id = p.team_id
            WHERE p.active = 1 AND (? = '%%' OR p.name_en LIKE ? OR p.name_ko LIKE ?)
            ORDER BY t.is_tracked DESC, p.name_ko, p.name_en""",
            (like, like, like),
        )

    def player(self, player_id: int):
        return self._one(
            """SELECT p.*, t.name AS team_name, t.short_name, t.is_tracked
            FROM players p JOIN teams t ON t.id = p.team_id WHERE p.id = ?""",
            (player_id,),
        )

    def batting_seasons(self, player_id: int):
        return self._all("SELECT * FROM batting_seasons WHERE player_id = ? ORDER BY season DESC", (player_id,))

    def pitching_seasons(self, player_id: int):
        return self._all("SELECT * FROM pitching_seasons WHERE player_id = ? ORDER BY season DESC", (player_id,))

    def awards(self, player_id: int):
        return self._all("SELECT season, award_name FROM awards WHERE player_id = ? ORDER BY season DESC", (player_id,))

    def milestones(self, tracked_only: bool = True, scope: str = "", search: str = ""):
        clauses = []
        params = []
        if scope:
            clauses.append("m.scope = ?")
            params.append(scope)
        if tracked_only:
            clauses.append("COALESCE(t.is_tracked, tt.is_tracked, 0) = 1")
        if search.strip():
            like = f"%{search.strip()}%"
            clauses.append("(m.label LIKE ? OR p.name_en LIKE ? OR p.name_ko LIKE ? OR t.name LIKE ?)")
            params.extend([like, like, like, like])
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        return self._all(
            f"""SELECT m.*, COALESCE(p.name_ko, p.name_en, t.name) AS entity_name,
            ROUND(CASE WHEN m.target_value <= 0 THEN 0 ELSE MIN(m.current_value / m.target_value * 100.0, 100) END, 1) AS progress,
            COALESCE(t.name, tt.name) AS team_name
            FROM milestones m
            LEFT JOIN players p ON m.entity_type = 'player' AND p.id = m.entity_id
            LEFT JOIN teams tt ON p.team_id = tt.id
            LEFT JOIN teams t ON m.entity_type = 'team' AND t.id = m.entity_id
            {where}
            ORDER BY m.achieved ASC, progress DESC, m.sort_order, entity_name""",
            tuple(params),
        )

    def player_milestones(self, player_id: int):
        return self._all(
            """SELECT *, ROUND(CASE WHEN target_value <= 0 THEN 0 ELSE MIN(current_value / target_value * 100.0, 100) END, 1) AS progress
            FROM milestones WHERE entity_type = 'player' AND entity_id = ?
            ORDER BY achieved ASC, scope, sort_order, target_value""",
            (player_id,),
        )

    def dashboard_summary(self):
        tracked = self.tracked_team()
        if not tracked:
            return {"team": "Not selected", "players": 0, "milestones": 0, "near": 0}
        player_count = self._one("SELECT COUNT(*) AS n FROM players WHERE team_id = ? AND active = 1", (tracked["id"],))["n"]
        rows = self.milestones(tracked_only=True)
        return {
            "team": tracked["name"],
            "players": player_count,
            "milestones": len(rows),
            "near": sum(1 for row in rows if not row["achieved"] and row["progress"] >= 90),
        }

    def get_setting(self, key: str, default: str = ""):
        row = self._one("SELECT value FROM app_settings WHERE key = ?", (key,))
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self.database.connect() as conn:
            conn.execute(
                "INSERT INTO app_settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
            conn.commit()

    def update_name_mapping(self, player_id: int, name_ko: str):
        with self.database.connect() as conn:
            conn.execute("UPDATE players SET name_ko = ? WHERE id = ?", (name_ko.strip(), player_id))
            conn.commit()

    def game_milestone_achievements(self, player_id: Optional[int] = None, tracked_only: bool = False):
        clauses = []
        params = []
        if player_id is not None:
            clauses.append("a.player_id = ?")
            params.append(player_id)
        if tracked_only:
            clauses.append("t.is_tracked = 1")

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        return self._all(
            f"""SELECT a.*, g.game_date, g.season, COALESCE(p.name_ko, p.name_en, 'Player #' || a.player_id) AS player_name,
            COALESCE(op.name_ko, op.name_en, '') AS opponent_name,
            ht.short_name AS home_team_short, at.short_name AS away_team_short
            FROM game_milestone_achievements a
            JOIN games g ON g.game_id = a.game_id
            LEFT JOIN players p ON p.id = a.player_id
            LEFT JOIN teams t ON t.id = p.team_id
            LEFT JOIN players op ON op.id = a.opponent_player_id
            LEFT JOIN teams ht ON ht.id = g.home_team_id
            LEFT JOIN teams at ON at.id = g.away_team_id
            {where}
            ORDER BY g.game_date DESC, a.id DESC""",
            tuple(params),
        )

    def get_game_milestone_rule_settings(self) -> Dict:
        """Read game_milestone_rule_settings table. Seed defaults if table is empty."""
        rows = self._all("SELECT * FROM game_milestone_rule_settings")
        if not rows:
            self.save_game_milestone_rule_settings(DEFAULT_GAME_MILESTONE_SETTINGS)
            return DEFAULT_GAME_MILESTONE_SETTINGS

        settings = {}
        for r in rows:
            key = r["family_key"]
            enabled = bool(r["enabled"])
            try:
                thresholds = json.loads(r["thresholds_json"])
            except Exception:
                thresholds = DEFAULT_GAME_MILESTONE_SETTINGS.get(key, {}).get("thresholds", [])
            settings[key] = {"enabled": enabled, "thresholds": thresholds}

        # Fill missing keys if any
        for key, default_val in DEFAULT_GAME_MILESTONE_SETTINGS.items():
            if key not in settings:
                settings[key] = default_val

        return settings

    def save_game_milestone_rule_settings(self, settings: Dict):
        """Save settings to game_milestone_rule_settings table transactionally."""
        with self.database.connect() as conn:
            for key, cfg in settings.items():
                enabled = 1 if cfg.get("enabled", True) else 0
                thresholds = cfg.get("thresholds", [])
                # Normalize thresholds: positive ints, unique, sorted ascending
                thresholds = sorted(list(dict.fromkeys(int(t) for t in thresholds if int(t) > 0)))
                conn.execute(
                    """INSERT INTO game_milestone_rule_settings (family_key, enabled, thresholds_json)
                    VALUES (?, ?, ?)
                    ON CONFLICT(family_key) DO UPDATE SET enabled=excluded.enabled, thresholds_json=excluded.thresholds_json""",
                    (key, enabled, json.dumps(thresholds)),
                )
            conn.commit()

    def rebuild_game_milestone_achievements(self, settings: Optional[Dict] = None):
        """Rebuild numeric family achievements from the stored Game Ledger after settings change."""
        if settings is None:
            settings = self.get_game_milestone_rule_settings()

        evaluator = GameMilestoneEvaluator(settings=settings)

        with self.database.connect() as conn:
            games_rows = conn.execute("SELECT * FROM games").fetchall()

            # Delete existing numeric family achievement rows
            conn.execute(
                """DELETE FROM game_milestone_achievements
                WHERE rule_key LIKE 'GAME_HITS_%'
                   OR rule_key LIKE 'GAME_RBI_%'
                   OR rule_key LIKE 'GAME_HR_%'
                   OR rule_key LIKE 'GAME_SB_%'
                   OR rule_key LIKE 'GAME_STRIKEOUTS_%'"""
            )

            for g_row in games_rows:
                game_id = g_row["game_id"]
                b_rows = conn.execute("SELECT * FROM player_game_batting WHERE game_id = ?", (game_id,)).fetchall()
                batting_lines = [
                    BattingLine(
                        player_id=b["player_id"],
                        name="",
                        team_id=b["team_id"],
                        ab=b["ab"],
                        r=b["r"],
                        h=b["h"],
                        rbi=b["rbi"],
                        bb=b["bb"],
                        so=b["so"],
                        lob=b["lob"],
                        doubles=b["doubles"],
                        triples=b["triples"],
                        hr=b["hr"],
                        sb=b["sb"],
                    )
                    for b in b_rows
                ]

                p_rows = conn.execute("SELECT * FROM player_game_pitching WHERE game_id = ?", (game_id,)).fetchall()
                pitching_lines = [
                    PitchingLine(
                        player_id=p["player_id"],
                        name="",
                        team_id=p["team_id"],
                        outs=p["outs"],
                        h=p["h"],
                        r=p["r"],
                        er=p["er"],
                        bb=p["bb"],
                        so=p["so"],
                        hr=p["hr"],
                        bf=p["bf"],
                        pitches=p["pitches"],
                        win=bool(p["win"]),
                        loss=bool(p["loss"]),
                        save=bool(p["save"]),
                        hold=bool(p["hold"]),
                    )
                    for p in p_rows
                ]

                ev_rows = conn.execute("SELECT * FROM game_batting_events WHERE game_id = ?", (game_id,)).fetchall()
                batting_events = [
                    BattingEvent(
                        game_id=game_id,
                        player_id=ev["player_id"],
                        event_index=ev["event_index"],
                        event_type=ev["event_type"],
                        season_total=ev["season_total"],
                        opponent_player_id=ev["opponent_player_id"],
                        context_text=ev["context_text"],
                    )
                    for ev in ev_rows
                ]

                rec = GameRecord(
                    game_id=game_id,
                    title="",
                    game_date=g_row["game_date"],
                    season=g_row["season"],
                    competition_type=g_row["competition_type"],
                    away_team_id=g_row["away_team_id"],
                    home_team_id=g_row["home_team_id"],
                    league_id=g_row["league_id"],
                    away_score=g_row["away_score"],
                    home_score=g_row["home_score"],
                    source_hash=g_row["source_hash"] or "",
                    batting_lines=batting_lines,
                    pitching_lines=pitching_lines,
                    batting_events=batting_events,
                )

                achs = evaluator.evaluate_game(rec)
                for ach in achs:
                    if any(
                        ach.rule_key.startswith(prefix)
                        for prefix in ("GAME_HITS_", "GAME_RBI_", "GAME_HR_", "GAME_SB_", "GAME_STRIKEOUTS_")
                    ):
                        conn.execute(
                            """INSERT OR IGNORE INTO game_milestone_achievements
                            (game_id, player_id, competition_type, rule_key, title, achieved_value, inning, half, opponent_player_id, context_text)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                ach.game_id,
                                ach.player_id if ach.player_id is not None else 0,
                                ach.competition_type,
                                ach.rule_key,
                                ach.title,
                                ach.achieved_value,
                                ach.inning,
                                ach.half,
                                ach.opponent_player_id,
                                ach.context_text,
                            ),
                        )
            conn.commit()

    def season_milestone_achievements(self, player_id: Optional[int] = None, tracked_only: bool = False):
        clauses = []
        params = []
        if player_id is not None:
            clauses.append("a.entity_id = ? AND a.entity_type = 'player'")
            params.append(player_id)
        if tracked_only:
            clauses.append("COALESCE(t.is_tracked, tt.is_tracked, 0) = 1")

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        return self._all(
            f"""SELECT a.*, COALESCE(p.name_ko, p.name_en, tt.name, 'ID #' || a.entity_id) AS entity_name,
            COALESCE(t.name, tt.name) AS team_name
            FROM season_milestone_achievements a
            LEFT JOIN players p ON a.entity_type = 'player' AND p.id = a.entity_id
            LEFT JOIN teams t ON t.id = p.team_id
            LEFT JOIN teams tt ON a.entity_type = 'team' AND tt.id = a.entity_id
            {where}
            ORDER BY a.season DESC, a.achieved_date DESC, a.id DESC""",
            tuple(params),
        )

    def current_season_state(self, season: int = 2027):
        tracked = self.tracked_team()
        tid = tracked["id"] if tracked else 0
        return self._one(
            "SELECT * FROM season_states WHERE season = ? AND tracked_team_id = ?", (season, tid)
        )

    def career_milestone_achievements(self, player_id: Optional[int] = None, tracked_only: bool = False):
        clauses = []
        params = []
        if player_id is not None:
            clauses.append("a.entity_id = ? AND a.entity_type = 'player'")
            params.append(player_id)
        if tracked_only:
            clauses.append("COALESCE(t.is_tracked, tt.is_tracked, 0) = 1")

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        return self._all(
            f"""SELECT a.*, COALESCE(p.name_ko, p.name_en, tt.name, 'ID #' || a.entity_id) AS entity_name,
            COALESCE(t.name, tt.name) AS team_name
            FROM career_milestone_achievements a
            LEFT JOIN players p ON a.entity_type = 'player' AND p.id = a.entity_id
            LEFT JOIN teams t ON t.id = p.team_id
            LEFT JOIN teams tt ON a.entity_type = 'team' AND tt.id = a.entity_id
            {where}
            ORDER BY a.achieved_date DESC, a.id DESC""",
            tuple(params),
        )
