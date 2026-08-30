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
