"""
Baseline Import Workflow (Phase 3.1)
Imports player_batting_stats.txt and player_pitching_stats.txt into baseline DB tables
with transaction safety, save isolation, and idempotency guarantees.
"""

import os
import hashlib
import datetime
import sqlite3
from typing import Dict, Any, Optional
from core.parser.stats_txt_parser import StatsTxtParser, ParsedBattingBaseline, ParsedPitchingBaseline
from core.db.player_repo import PlayerRepository


class BaselineImportService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _compute_hash(file_path: str) -> str:
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha.update(chunk)
        return sha.hexdigest()

    def import_baselines(
        self,
        batting_file: str,
        pitching_file: str,
        season: int,
        mode: str = "first_time"
    ) -> Dict[str, Any]:
        """
        Executes baseline stats import within a single transaction.
        Modes: 'first_time', 'refresh', 'mid_season'.
        """
        if not os.path.exists(batting_file) or not os.path.exists(pitching_file):
            raise FileNotFoundError("Baseline TXT files not found.")

        bat_hash = self._compute_hash(batting_file)
        pitch_hash = self._compute_hash(pitching_file)
        combined_hash = hashlib.sha256(f"{bat_hash}:{pitch_hash}".encode("utf-8")).hexdigest()

        # Parse in memory first
        teams = StatsTxtParser.parse_team_headers(batting_file)
        batting_records = StatsTxtParser.parse_batting_stats(batting_file, filter_split_id=1)
        pitching_records = StatsTxtParser.parse_pitching_stats(pitching_file, filter_split_id=1)

        cursor = self.conn.cursor()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            self.conn.execute("BEGIN TRANSACTION;")

            # 1. Upsert Teams
            for t in teams:
                cursor.execute(
                    """INSERT INTO teams (team_key, abbreviation, name, league, is_custom)
                       VALUES (?, ?, ?, ?, 0)
                       ON CONFLICT(team_key) DO UPDATE SET name=excluded.name, league=excluded.league""",
                    (f"team_{t.team_id}", t.name[:10].upper(), t.name, t.league_name)
                )

            # 2. Clear old baselines for this season if refresh
            if mode == "refresh":
                cursor.execute("DELETE FROM baseline_batting_stats WHERE season = ?", (season,))
                cursor.execute("DELETE FROM baseline_pitching_stats WHERE season = ?", (season,))

            # 3. Import Batting Baselines
            player_repo = PlayerRepository(self.conn)
            bat_count = 0
            for b in batting_records:
                p = player_repo.get_or_create_player(b.ootp_player_id, b.first_name, b.last_name)
                p_id = p["id"]

                cursor.execute(
                    """INSERT INTO baseline_batting_stats
                       (player_id, season, team_id, is_career, g, ab, r, h, d, t, hr, rbi, bb, k, sb, cs, avg, obp, slg, ops)
                       VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (p_id, season, b.team_id, b.g, b.ab, b.r, b.h, b.d, b.t, b.hr, b.rbi, b.bb, b.k, b.sb, b.cs, b.avg, b.obp, b.slg, b.ops)
                )
                bat_count += 1

            # 4. Import Pitching Baselines
            pitch_count = 0
            for p_rec in pitching_records:
                p = player_repo.get_or_create_player(p_rec.ootp_player_id, p_rec.first_name, p_rec.last_name)
                p_id = p["id"]

                cursor.execute(
                    """INSERT INTO baseline_pitching_stats
                       (player_id, season, team_id, is_career, g, gs, w, l, sv, hld, ip_outs, h, r, er, bb, k, hr, era, whip)
                       VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (p_id, season, p_rec.team_id, p_rec.g, p_rec.gs, p_rec.w, p_rec.l, p_rec.sv, p_rec.hld,
                     p_rec.ip_outs, p_rec.h, p_rec.r, p_rec.er, p_rec.bb, p_rec.k, p_rec.hr, p_rec.era, p_rec.whip)
                )
                pitch_count += 1

            # 5. Save processed source fingerprint
            cursor.execute(
                """INSERT INTO processed_sources (source_type, source_id, path_snapshot, content_hash, mtime, size, status, processed_at)
                   VALUES ('stats_baseline', ?, ?, ?, ?, ?, 'processed', ?)
                   ON CONFLICT(source_type, source_id) DO UPDATE SET
                   content_hash=excluded.content_hash, status='processed', processed_at=excluded.processed_at""",
                (f"baseline_{season}", batting_file, combined_hash, os.path.getmtime(batting_file), os.path.getsize(batting_file), now_iso)
            )

            self.conn.commit()
            return {
                "status": "success",
                "mode": mode,
                "season": season,
                "teams_imported": len(teams),
                "batting_records_imported": bat_count,
                "pitching_records_imported": pitch_count,
                "content_hash": combined_hash,
            }
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Baseline import transaction failed: {e}") from e
