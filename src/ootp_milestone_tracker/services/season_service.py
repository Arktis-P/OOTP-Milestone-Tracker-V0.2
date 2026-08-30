import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..db.database import Database
from ..importer.game_models import GameRecord
from ..milestones.season_models import SeasonMilestoneAchievement
from ..milestones.season_rules import DEFAULT_SEASON_MILESTONE_SETTINGS, evaluate_season_rate_milestones


class SeasonService:
    def __init__(self, database: Database):
        self.database = database

    def get_season_settings(self) -> Dict:
        with self.database.connect() as conn:
            rows = conn.execute("SELECT * FROM season_milestone_rule_settings").fetchall()
            if not rows:
                self.save_season_settings(DEFAULT_SEASON_MILESTONE_SETTINGS)
                return DEFAULT_SEASON_MILESTONE_SETTINGS

            settings = {}
            for r in rows:
                key = r["family_key"]
                enabled = bool(r["enabled"])
                try:
                    thresholds = json.loads(r["thresholds_json"])
                except Exception:
                    thresholds = DEFAULT_SEASON_MILESTONE_SETTINGS.get(key, {}).get("thresholds", [])
                settings[key] = {"enabled": enabled, "thresholds": thresholds}

            for key, default_val in DEFAULT_SEASON_MILESTONE_SETTINGS.items():
                if key not in settings:
                    settings[key] = default_val

            return settings

    def save_season_settings(self, settings: Dict):
        with self.database.connect() as conn:
            for key, cfg in settings.items():
                if key == "GENERAL":
                    conn.execute(
                        """INSERT INTO season_milestone_rule_settings (family_key, enabled, thresholds_json)
                        VALUES (?, 1, ?)
                        ON CONFLICT(family_key) DO UPDATE SET thresholds_json=excluded.thresholds_json""",
                        (key, json.dumps(cfg)),
                    )
                else:
                    enabled = 1 if cfg.get("enabled", True) else 0
                    thresholds = cfg.get("thresholds", [])
                    thresholds = sorted(list(dict.fromkeys(thresholds)))
                    conn.execute(
                        """INSERT INTO season_milestone_rule_settings (family_key, enabled, thresholds_json)
                        VALUES (?, ?, ?)
                        ON CONFLICT(family_key) DO UPDATE SET enabled=excluded.enabled, thresholds_json=excluded.thresholds_json""",
                        (key, enabled, json.dumps(thresholds)),
                    )
            conn.commit()

    def rebuild_season(self, season: int, settings: Optional[Dict] = None):
        settings = settings or self.get_season_settings()
        with self.database.connect() as conn:
            # 1. Reset live totals for season
            conn.execute("DELETE FROM batting_seasons WHERE season = ? AND status = 'live'", (season,))
            conn.execute("DELETE FROM pitching_seasons WHERE season = ? AND status = 'live'", (season,))
            conn.execute("DELETE FROM team_seasons WHERE season = ?", (season,))
            conn.execute("DELETE FROM season_milestone_achievements WHERE season = ? AND source = 'game_crossing'", (season,))

            # 2. Get games sorted chronologically
            games = conn.execute(
                "SELECT * FROM games WHERE season = ? ORDER BY game_date ASC, game_id ASC", (season,)
            ).fetchall()

            # Running trackers
            batting_cum: Dict[Tuple[int, str], Dict] = {}
            pitching_cum: Dict[Tuple[int, str], Dict] = {}
            team_cum: Dict[Tuple[int, str], Dict] = {}

            # Configured thresholds
            hits_cfg = settings.get("SEASON_HITS", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_HITS"])
            hr_cfg = settings.get("SEASON_HR", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_HR"])
            rbi_cfg = settings.get("SEASON_RBI", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_RBI"])
            runs_cfg = settings.get("SEASON_RUNS", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_RUNS"])
            sb_cfg = settings.get("SEASON_SB", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_SB"])

            ip_cfg = settings.get("SEASON_IP", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_IP"])
            so_cfg = settings.get("SEASON_STRIKEOUTS", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_STRIKEOUTS"])
            win_cfg = settings.get("SEASON_WINS", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_WINS"])
            hold_cfg = settings.get("SEASON_HOLDS", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_HOLDS"])
            sv_cfg = settings.get("SEASON_SAVES", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_SAVES"])
            team_win_cfg = settings.get("TEAM_WINS", DEFAULT_SEASON_MILESTONE_SETTINGS["TEAM_WINS"])

            for g in games:
                game_id = g["game_id"]
                game_date = g["game_date"]
                comp = g["competition_type"]

                # Process Batting
                b_lines = conn.execute("SELECT * FROM player_game_batting WHERE game_id = ?", (game_id,)).fetchall()
                for b in b_lines:
                    pid = b["player_id"]
                    key = (pid, comp)
                    tot = batting_cum.setdefault(
                        key, {"h": 0, "hr": 0, "rbi": 0, "r": 0, "sb": 0, "ab": 0, "bb": 0, "so": 0, "doubles": 0, "triples": 0, "g": 0}
                    )
                    prev_h, prev_hr, prev_rbi, prev_r, prev_sb = tot["h"], tot["hr"], tot["rbi"], tot["r"], tot["sb"]

                    tot["g"] += 1
                    tot["ab"] += b["ab"]
                    tot["h"] += b["h"]
                    tot["doubles"] += b["doubles"]
                    tot["triples"] += b["triples"]
                    tot["hr"] += b["hr"]
                    tot["rbi"] += b["rbi"]
                    tot["r"] += b["r"]
                    tot["bb"] += b["bb"]
                    tot["so"] += b["so"]
                    tot["sb"] += b["sb"]

                    # Check thresholds
                    if comp == "regular_season":
                        self._check_crossing(conn, "player", pid, season, comp, "SEASON_HITS", "시즌 {}안타", prev_h, tot["h"], hits_cfg, game_id, game_date)
                        self._check_crossing(conn, "player", pid, season, comp, "SEASON_HR", "시즌 {}홈런", prev_hr, tot["hr"], hr_cfg, game_id, game_date)
                        self._check_crossing(conn, "player", pid, season, comp, "SEASON_RBI", "시즌 {}타점", prev_rbi, tot["rbi"], rbi_cfg, game_id, game_date)
                        self._check_crossing(conn, "player", pid, season, comp, "SEASON_RUNS", "시즌 {}득점", prev_r, tot["r"], runs_cfg, game_id, game_date)
                        self._check_crossing(conn, "player", pid, season, comp, "SEASON_SB", "시즌 {}도루", prev_sb, tot["sb"], sb_cfg, game_id, game_date)

                # Process Pitching
                p_lines = conn.execute("SELECT * FROM player_game_pitching WHERE game_id = ?", (game_id,)).fetchall()
                for p in p_lines:
                    pid = p["player_id"]
                    key = (pid, comp)
                    tot = pitching_cum.setdefault(
                        key, {"outs": 0, "so": 0, "w": 0, "l": 0, "sv": 0, "holds": 0, "h": 0, "r": 0, "er": 0, "bb": 0, "bf": 0, "g": 0, "gs": 0}
                    )
                    prev_outs, prev_so, prev_w, prev_holds, prev_sv = tot["outs"], tot["so"], tot["w"], tot["holds"], tot["sv"]

                    tot["g"] += 1
                    if p["outs"] >= 15:
                        tot["gs"] += 1
                    tot["outs"] += p["outs"]
                    tot["so"] += p["so"]
                    tot["w"] += p["win"]
                    tot["l"] += p["loss"]
                    tot["sv"] += p["save"]
                    tot["holds"] += p["hold"]
                    tot["h"] += p["h"]
                    tot["r"] += p["r"]
                    tot["er"] += p["er"]
                    tot["bb"] += p["bb"]
                    tot["bf"] += p["bf"]

                    if comp == "regular_season":
                        # IP thresholds in outs (threshold * 3)
                        if ip_cfg.get("enabled", True):
                            for ip_val in ip_cfg.get("thresholds", []):
                                t_outs = ip_val * 3
                                if prev_outs < t_outs <= tot["outs"]:
                                    self._save_achievement(
                                        conn, "player", pid, season, comp, f"SEASON_IP_{ip_val}", f"시즌 {ip_val}이닝", ip_val, tot["outs"] / 3.0, game_id, game_date
                                    )
                        self._check_crossing(conn, "player", pid, season, comp, "SEASON_STRIKEOUTS", "시즌 {}탈삼진", prev_so, tot["so"], so_cfg, game_id, game_date)
                        self._check_crossing(conn, "player", pid, season, comp, "SEASON_WINS", "시즌 {}승", prev_w, tot["w"], win_cfg, game_id, game_date)
                        self._check_crossing(conn, "player", pid, season, comp, "SEASON_HOLDS", "시즌 {}홀드", prev_holds, tot["holds"], hold_cfg, game_id, game_date)
                        self._check_crossing(conn, "player", pid, season, comp, "SEASON_SAVES", "시즌 {}세이브", prev_sv, tot["sv"], sv_cfg, game_id, game_date)

                # Process Team Wins
                home_id, away_id = g["home_team_id"], g["away_team_id"]
                home_score, away_score = g["home_score"], g["away_score"]
                if comp == "regular_season" and home_score != away_score:
                    win_team = home_id if home_score > away_score else away_id
                    key = (win_team, comp)
                    tot = team_cum.setdefault(key, {"w": 0, "g": 0})
                    prev_w = tot["w"]
                    tot["w"] += 1
                    tot["g"] += 1
                    self._check_crossing(conn, "team", win_team, season, comp, "TEAM_WINS", "시즌 {}승", prev_w, tot["w"], team_win_cfg, game_id, game_date)

            # Persist Live Batting Seasons
            for (pid, comp), tot in batting_cum.items():
                ab = tot["ab"]
                pa = ab + tot["bb"]
                avg = tot["h"] / ab if ab > 0 else 0.0
                obp = (tot["h"] + tot["bb"]) / pa if pa > 0 else 0.0
                singles = tot["h"] - tot["doubles"] - tot["triples"] - tot["hr"]
                slg = (singles + 2 * tot["doubles"] + 3 * tot["triples"] + 4 * tot["hr"]) / ab if ab > 0 else 0.0
                ops = obp + slg

                conn.execute(
                    """INSERT INTO batting_seasons (player_id, season, competition_type, g, pa, ab, h, doubles, triples, hr, rbi, r, bb, so, sb, avg, obp, slg, ops, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'live')
                    ON CONFLICT(player_id, season, competition_type) DO UPDATE SET
                    g=excluded.g, pa=excluded.pa, ab=excluded.ab, h=excluded.h, doubles=excluded.doubles, triples=excluded.triples,
                    hr=excluded.hr, rbi=excluded.rbi, r=excluded.r, bb=excluded.bb, so=excluded.so, sb=excluded.sb,
                    avg=excluded.avg, obp=excluded.obp, slg=excluded.slg, ops=excluded.ops""",
                    (pid, season, comp, tot["g"], pa, ab, tot["h"], tot["doubles"], tot["triples"], tot["hr"], tot["rbi"], tot["r"], tot["bb"], tot["so"], tot["sb"], avg, obp, slg, ops),
                )

            # Persist Live Pitching Seasons
            for (pid, comp), tot in pitching_cum.items():
                outs = tot["outs"]
                era = (tot["er"] * 27.0) / outs if outs > 0 else 0.0
                whip = ((tot["h"] + tot["bb"]) * 3.0) / outs if outs > 0 else 0.0
                conn.execute(
                    """INSERT INTO pitching_seasons (player_id, season, competition_type, g, gs, w, l, sv, outs, ip, so, h, r, er, bb, bf, holds, era, whip, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'live')
                    ON CONFLICT(player_id, season, competition_type) DO UPDATE SET
                    g=excluded.g, gs=excluded.gs, w=excluded.w, l=excluded.l, sv=excluded.sv, outs=excluded.outs, ip=excluded.ip,
                    so=excluded.so, h=excluded.h, r=excluded.r, er=excluded.er, bb=excluded.bb, bf=excluded.bf, holds=excluded.holds,
                    era=excluded.era, whip=excluded.whip""",
                    (pid, season, comp, tot["g"], tot["gs"], tot["w"], tot["l"], tot["sv"], outs, outs / 3.0, tot["so"], tot["h"], tot["r"], tot["er"], tot["bb"], tot["bf"], tot["holds"], era, whip),
                )

            # Persist Team Seasons
            for (tid, comp), tot in team_cum.items():
                conn.execute(
                    """INSERT INTO team_seasons (team_id, season, competition_type, g, w, l)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(team_id, season, competition_type) DO UPDATE SET g=excluded.g, w=excluded.w""",
                    (tid, season, comp, tot["g"], tot["w"], tot["g"] - tot["w"]),
                )

            conn.commit()

    def _check_crossing(
        self, conn, entity_type: str, entity_id: int, season: int, comp: str, family_key: str, title_fmt: str, prev_val: int, curr_val: int, cfg: Dict, game_id: int, game_date: str
    ):
        if not cfg.get("enabled", True):
            return
        for t in cfg.get("thresholds", []):
            if prev_val < t <= curr_val:
                self._save_achievement(
                    conn, entity_type, entity_id, season, comp, f"{family_key}_{t}", title_fmt.format(t), t, float(curr_val), game_id, game_date
                )

    def _save_achievement(
        self, conn, entity_type: str, entity_id: int, season: int, comp: str, rule_key: str, title: str, threshold: float, achieved_val: float, game_id: Optional[int], game_date: Optional[str]
    ):
        conn.execute(
            """INSERT OR IGNORE INTO season_milestone_achievements
            (entity_type, entity_id, season, competition_type, rule_key, title, threshold_value, achieved_value, achieved_game_id, achieved_date, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'game_crossing')""",
            (entity_type, entity_id, season, comp, rule_key, title, threshold, achieved_val, game_id, game_date),
        )

    def check_finalization_eligibility(self, season: int, tracked_team_id: int) -> Tuple[int, int, bool]:
        with self.database.connect() as conn:
            settings = self.get_season_settings()
            target_games = settings.get("GENERAL", {}).get("regular_season_game_target", 162)

            count_row = conn.execute(
                """SELECT COUNT(DISTINCT game_id) AS n FROM games
                WHERE season = ? AND competition_type = 'regular_season'
                  AND (home_team_id = ? OR away_team_id = ?)""",
                (season, tracked_team_id, tracked_team_id),
            ).fetchone()
            processed_games = count_row["n"] if count_row else 0

            is_eligible = processed_games >= target_games
            return processed_games, target_games, is_eligible

    def finalize_season(
        self, season: int, tracked_team_id: int, export_dir: Optional[Path] = None, continue_without_export: bool = False
    ) -> Dict:
        """Finalize regular season with reconciliation if export_dir supplied, else unreconciled."""
        with self.database.connect() as conn:
            processed_games, target_games, is_eligible = self.check_finalization_eligibility(season, tracked_team_id)
            if not is_eligible and not continue_without_export:
                raise ValueError(f"Season {season} is not eligible to finalize. ({processed_games}/{target_games} games processed)")

            settings = self.get_season_settings()

            if export_dir and export_dir.exists():
                b_file = export_dir / "player_batting_stats.txt"
                p_file = export_dir / "player_pitching_stats.txt"

                if b_file.exists() and p_file.exists():
                    # Process Reconciled Export
                    reconciled_count, adj_count = self._reconcile_exports(conn, season, b_file, p_file, settings)
                    # Evaluate Rate Milestones
                    b_rows = [dict(r) for r in conn.execute("SELECT * FROM batting_seasons WHERE season = ?", (season,)).fetchall()]
                    p_rows = [dict(r) for r in conn.execute("SELECT * FROM pitching_seasons WHERE season = ?", (season,)).fetchall()]
                    rate_achs = evaluate_season_rate_milestones(b_rows, p_rows, settings)

                    for ach in rate_achs:
                        conn.execute(
                            """INSERT OR IGNORE INTO season_milestone_achievements
                            (entity_type, entity_id, season, competition_type, rule_key, title, threshold_value, achieved_value, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (ach.entity_type, ach.entity_id, ach.season, ach.competition_type, ach.rule_key, ach.title, ach.threshold_value, ach.achieved_value, ach.source),
                        )

                    conn.execute(
                        """INSERT INTO season_states (season, tracked_team_id, competition_type, regular_season_game_target, processed_team_games, status, finalized_at)
                        VALUES (?, ?, 'regular_season', ?, ?, 'finalized_reconciled', ?)
                        ON CONFLICT(season, tracked_team_id, competition_type) DO UPDATE SET
                        processed_team_games=excluded.processed_team_games, status='finalized_reconciled', finalized_at=excluded.finalized_at""",
                        (season, tracked_team_id, target_games, processed_games, datetime.now().isoformat()),
                    )
                    conn.commit()
                    return {
                        "status": "finalized_reconciled",
                        "players_reconciled": reconciled_count,
                        "adjustments": adj_count,
                        "rate_milestones": len(rate_achs),
                    }

            # Fallback: Continue without export
            b_rows = [dict(r) for r in conn.execute("SELECT * FROM batting_seasons WHERE season = ?", (season,)).fetchall()]
            p_rows = [dict(r) for r in conn.execute("SELECT * FROM pitching_seasons WHERE season = ?", (season,)).fetchall()]
            rate_achs = evaluate_season_rate_milestones(b_rows, p_rows, settings)
            for ach in rate_achs:
                conn.execute(
                    """INSERT OR IGNORE INTO season_milestone_achievements
                    (entity_type, entity_id, season, competition_type, rule_key, title, threshold_value, achieved_value, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (ach.entity_type, ach.entity_id, ach.season, ach.competition_type, ach.rule_key, ach.title, ach.threshold_value, ach.achieved_value, ach.source),
                )

            conn.execute(
                """INSERT INTO season_states (season, tracked_team_id, competition_type, regular_season_game_target, processed_team_games, status, finalized_at)
                VALUES (?, ?, 'regular_season', ?, ?, 'finalized_unreconciled', ?)
                ON CONFLICT(season, tracked_team_id, competition_type) DO UPDATE SET
                processed_team_games=excluded.processed_team_games, status='finalized_unreconciled', finalized_at=excluded.finalized_at""",
                (season, tracked_team_id, target_games, processed_games, datetime.now().isoformat()),
            )
            conn.commit()
            return {
                "status": "finalized_unreconciled",
                "players_reconciled": 0,
                "adjustments": 0,
                "rate_milestones": len(rate_achs),
            }

    def _reconcile_exports(self, conn, season: int, b_file: Path, p_file: Path, settings: Dict) -> Tuple[int, int]:
        # Create Checkpoint
        b_hash = hashlib.sha256(b_file.read_bytes()).hexdigest()
        p_hash = hashlib.sha256(p_file.read_bytes()).hexdigest()
        cur = conn.execute(
            """INSERT INTO stats_checkpoints (checkpoint_type, season, created_at, source_paths, source_hashes)
            VALUES ('regular_season_final', ?, ?, ?, ?)""",
            (season, datetime.now().isoformat(), f"{b_file.name};{p_file.name}", f"{b_hash};{p_hash}"),
        )
        checkpoint_id = cur.lastrowid

        reconciled_players = set()
        adj_count = 0

        # Parse Batting Export CSV lines
        b_lines = [l for l in b_file.read_text(encoding="utf-8", errors="replace").splitlines() if not l.startswith("//")]
        for l in b_lines:
            parts = [p.strip() for p in l.split(",")]
            if len(parts) >= 28 and parts[27] == "1":  # split_id = 1 (regular season)
                try:
                    pid = int(parts[0])
                    yr = int(parts[3])
                    if yr != season:
                        continue
                    reconciled_players.add(pid)

                    g, pa, ab, h, d, t, hr, rbi, r, sb, cs, bb, hp, k, sh, sf = (
                        int(parts[5]), int(parts[7]), int(parts[8]), int(parts[9]), int(parts[10]), int(parts[11]),
                        int(parts[12]), int(parts[13]), int(parts[14]), int(parts[15]), int(parts[16]), int(parts[17]),
                        int(parts[18]), int(parts[19]), int(parts[20]), int(parts[21])
                    )

                    avg = h / ab if ab > 0 else 0.0
                    obp = (h + bb + hp) / (ab + bb + hp + sf) if (ab + bb + hp + sf) > 0 else 0.0
                    singles = h - d - t - hr
                    slg = (singles + 2*d + 3*t + 4*hr) / ab if ab > 0 else 0.0
                    ops = obp + slg

                    # Check ledger differences
                    led = conn.execute("SELECT * FROM batting_seasons WHERE player_id = ? AND season = ?", (pid, season)).fetchone()
                    if led:
                        diff = h - led["h"]
                        if diff != 0:
                            adj_count += 1
                            conn.execute(
                                """INSERT INTO season_reconciliation_records (checkpoint_id, player_id, season, stat_key, ledger_value, export_value, adjustment, created_at)
                                VALUES (?, ?, ?, 'h', ?, ?, ?, ?)""",
                                (checkpoint_id, pid, season, float(led["h"]), float(h), float(diff), datetime.now().isoformat()),
                            )

                    conn.execute(
                        """INSERT INTO batting_seasons (player_id, season, competition_type, g, pa, ab, h, doubles, triples, hr, rbi, r, bb, so, sb, cs, hbp, sf, sh, avg, obp, slg, ops, status)
                        VALUES (?, ?, 'regular_season', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'reconciled')
                        ON CONFLICT(player_id, season, competition_type) DO UPDATE SET
                        g=excluded.g, pa=excluded.pa, ab=excluded.ab, h=excluded.h, doubles=excluded.doubles, triples=excluded.triples,
                        hr=excluded.hr, rbi=excluded.rbi, r=excluded.r, bb=excluded.bb, so=excluded.so, sb=excluded.sb,
                        cs=excluded.cs, hbp=excluded.hbp, sf=excluded.sf, sh=excluded.sh, avg=excluded.avg, obp=excluded.obp, slg=excluded.slg, ops=excluded.ops, status='reconciled'""",
                        (pid, season, g, pa, ab, h, d, t, hr, rbi, r, sb, cs, bb, hp, k, sh, sf, avg, obp, slg, ops),
                    )
                except (ValueError, IndexError):
                    pass

        # Parse Pitching Export CSV lines
        p_lines = [l for l in p_file.read_text(encoding="utf-8", errors="replace").splitlines() if not l.startswith("//")]
        for l in p_lines:
            parts = [p.strip() for p in l.split(",")]
            if len(parts) >= 47 and parts[46] == "1":  # split_id = 1
                try:
                    pid = int(parts[0])
                    yr = int(parts[3])
                    if yr != season:
                        continue
                    reconciled_players.add(pid)

                    g, gs, w, l_val, sv = int(parts[5]), int(parts[6]), int(parts[7]), int(parts[8]), int(parts[9])
                    ip_str = parts[10]
                    full_ip = int(float(ip_str))
                    decimal_ip = int(round((float(ip_str) - full_ip) * 10)) if "." in ip_str else 0
                    outs = full_ip * 3 + decimal_ip

                    ha, r_val, er, bb, hp, k, bf, hr = int(parts[11]), int(parts[12]), int(parts[13]), int(parts[14]), int(parts[15]), int(parts[16]), int(parts[17]), int(parts[22])
                    holds = int(parts[37]) if len(parts) > 37 else 0

                    era = (er * 27.0) / outs if outs > 0 else 0.0
                    whip = ((ha + bb) * 3.0) / outs if outs > 0 else 0.0

                    conn.execute(
                        """INSERT INTO pitching_seasons (player_id, season, competition_type, g, gs, w, l, sv, outs, ip, so, h, r, er, bb, bf, holds, era, whip, status)
                        VALUES (?, ?, 'regular_season', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'reconciled')
                        ON CONFLICT(player_id, season, competition_type) DO UPDATE SET
                        g=excluded.g, gs=excluded.gs, w=excluded.w, l=excluded.l, sv=excluded.sv, outs=excluded.outs, ip=excluded.ip,
                        so=excluded.so, h=excluded.h, r=excluded.r, er=excluded.er, bb=excluded.bb, bf=excluded.bf, holds=excluded.holds,
                        era=excluded.era, whip=excluded.whip, status='reconciled'""",
                        (pid, season, g, gs, w, l_val, sv, outs, outs / 3.0, k, ha, r_val, er, bb, bf, holds, era, whip),
                    )
                except (ValueError, IndexError):
                    pass

        return len(reconciled_players), adj_count
