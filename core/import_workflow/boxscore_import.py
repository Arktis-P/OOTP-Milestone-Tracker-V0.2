"""
Boxscore Import Workflow (Phase 3.2, 3.3, 3.4)
Handles single & batch boxscore file imports with idempotency (content_hash fingerprinting),
modified boxscore re-importing with atomic rollback, and folder scanning.
"""

import os
import glob
import hashlib
import datetime
import sqlite3
from typing import Dict, Any, List, Optional
from core.parser.boxscore_parser import BoxscoreParser, ParsedBoxscore
from core.db.player_repo import PlayerRepository


class BoxscoreImportService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha.update(chunk)
        return sha.hexdigest()

    def import_boxscore(self, html_path: str, force_reimport: bool = False) -> Dict[str, Any]:
        """
        Imports a single game_box_XXXX.html file into SQLite DB inside a single transaction.
        Handles modified boxscore re-imports idempotently.
        """
        if not os.path.exists(html_path):
            raise FileNotFoundError(f"Boxscore file not found: {html_path}")

        filename = os.path.basename(html_path)
        content_hash = self.compute_file_hash(html_path)
        source_id = os.path.splitext(filename)[0]

        cursor = self.conn.cursor()

        # 1. Check idempotency & processed source state
        cursor.execute(
            "SELECT content_hash, status FROM processed_sources WHERE source_type = 'boxscore' AND source_id = ?",
            (source_id,)
        )
        row = cursor.fetchone()
        if row and not force_reimport:
            existing_hash, status = row[0], row[1]
            if existing_hash == content_hash and status == "processed":
                return {
                    "status": "unchanged",
                    "source_id": source_id,
                    "content_hash": content_hash,
                    "message": "Boxscore file already processed and content hash is identical."
                }

        # 2. Parse HTML in memory
        boxscore = BoxscoreParser.parse_file(html_path)
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        player_repo = PlayerRepository(self.conn)

        try:
            self.conn.execute("BEGIN TRANSACTION;")

            # 3. Handle modified boxscore re-import (clean old stats/game if present)
            cursor.execute(
                "SELECT id FROM games WHERE season = ? AND ootp_game_id = ?",
                (boxscore.season, boxscore.ootp_game_id)
            )
            game_row = cursor.fetchone()
            game_id = game_row[0] if game_row else None

            if game_id:
                # Remove old stats and auto milestones for this game ID
                cursor.execute("DELETE FROM batting_game_stats WHERE game_id = ?", (game_id,))
                cursor.execute("DELETE FROM pitching_game_stats WHERE game_id = ?", (game_id,))
                cursor.execute("DELETE FROM milestone_events WHERE game_id = ? AND source_type = 'auto'", (game_id,))

            # 4. Upsert Teams
            away_team_key = f"team_{boxscore.away_team_name.lower().replace(' ', '_')}"
            home_team_key = f"team_{boxscore.home_team_name.lower().replace(' ', '_')}"

            cursor.execute(
                "INSERT INTO teams (team_key, abbreviation, name, is_custom) VALUES (?, ?, ?, 0) ON CONFLICT(team_key) DO UPDATE SET name=excluded.name",
                (away_team_key, boxscore.away_team_name[:10].upper(), boxscore.away_team_name)
            )
            cursor.execute("SELECT id FROM teams WHERE team_key = ?", (away_team_key,))
            away_team_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO teams (team_key, abbreviation, name, is_custom) VALUES (?, ?, ?, 0) ON CONFLICT(team_key) DO UPDATE SET name=excluded.name",
                (home_team_key, boxscore.home_team_name[:10].upper(), boxscore.home_team_name)
            )
            cursor.execute("SELECT id FROM teams WHERE team_key = ?", (home_team_key,))
            home_team_id = cursor.fetchone()[0]

            # 5. Insert/Update Game
            if not game_id:
                cursor.execute(
                    """INSERT INTO games (season, ootp_game_id, game_date, home_team_id, away_team_id, game_type, source_id, source_hash)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (boxscore.season, boxscore.ootp_game_id, boxscore.game_date, home_team_id, away_team_id, boxscore.game_type, source_id, content_hash)
                )
                game_id = cursor.lastrowid
            else:
                cursor.execute(
                    """UPDATE games SET game_date = ?, home_team_id = ?, away_team_id = ?, source_hash = ?
                       WHERE id = ?""",
                    (boxscore.game_date, home_team_id, away_team_id, content_hash, game_id)
                )

            # 6. Insert Batting Game Stats
            for b in boxscore.batting_lines:
                # Name split
                parts = b.display_name.split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""

                p = player_repo.get_or_create_player(b.ootp_player_id, first_name, last_name, display_name=b.display_name)
                p_id = p["id"]
                t_id = home_team_id if b.team_name == boxscore.home_team_name else away_team_id

                cursor.execute(
                    """INSERT INTO batting_game_stats
                       (game_id, player_id, team_id, ab, r, h, d, t, hr, rbi, bb, k, sb, cs, sh, sf, hbp, raw_notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(game_id, player_id) DO UPDATE SET
                       ab=excluded.ab, r=excluded.r, h=excluded.h, rbi=excluded.rbi, bb=excluded.bb, k=excluded.k""",
                    (game_id, p_id, t_id, b.ab, b.r, b.h, b.d, b.t, b.hr, b.rbi, b.bb, b.k, b.sb, b.cs, b.sh, b.sf, b.hbp, b.raw_notes)
                )

            # 7. Insert Pitching Game Stats
            for p_line in boxscore.pitching_lines:
                parts = p_line.display_name.split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""

                p = player_repo.get_or_create_player(p_line.ootp_player_id, first_name, last_name, display_name=p_line.display_name)
                p_id = p["id"]
                t_id = home_team_id if p_line.team_name == boxscore.home_team_name else away_team_id

                cursor.execute(
                    """INSERT INTO pitching_game_stats
                       (game_id, player_id, team_id, ip_outs, h, r, er, bb, k, hr, w, l, sv, hld, cg, sho, raw_notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(game_id, player_id) DO UPDATE SET
                       ip_outs=excluded.ip_outs, h=excluded.h, r=excluded.r, er=excluded.er, bb=excluded.bb, k=excluded.k""",
                    (game_id, p_id, t_id, p_line.ip_outs, p_line.h, p_line.r, p_line.er, p_line.bb, p_line.k, p_line.hr,
                     p_line.w, p_line.l, p_line.sv, p_line.hld, p_line.cg, p_line.sho, p_line.raw_notes)
                )

            # 8. Save Processed Source Fingerprint
            cursor.execute(
                """INSERT INTO processed_sources (source_type, source_id, path_snapshot, content_hash, mtime, size, status, processed_at)
                   VALUES ('boxscore', ?, ?, ?, ?, ?, 'processed', ?)
                   ON CONFLICT(source_type, source_id) DO UPDATE SET
                   content_hash=excluded.content_hash, status='processed', processed_at=excluded.processed_at""",
                (source_id, html_path, content_hash, os.path.getmtime(html_path), os.path.getsize(html_path), now_iso)
            )

            self.conn.commit()
            return {
                "status": "success",
                "game_id": game_id,
                "source_id": source_id,
                "season": boxscore.season,
                "game_date": boxscore.game_date,
                "batting_count": len(boxscore.batting_lines),
                "pitching_count": len(boxscore.pitching_lines),
                "special_events_count": len(boxscore.special_events),
                "content_hash": content_hash,
            }
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Boxscore import transaction failed for {filename}: {e}") from e

    def import_boxscores_dir(self, boxscores_dir: str) -> Dict[str, Any]:
        """Scans directory and imports all game_box_*.html files sequentially."""
        pattern = os.path.join(boxscores_dir, "game_box_*.html")
        files = glob.glob(pattern)

        success_count = 0
        unchanged_count = 0
        error_count = 0
        errors: List[str] = []

        for f_path in sorted(files):
            try:
                res = self.import_boxscore(f_path)
                if res["status"] == "success":
                    success_count += 1
                elif res["status"] == "unchanged":
                    unchanged_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"{os.path.basename(f_path)}: {e}")

        return {
            "total_found": len(files),
            "imported": success_count,
            "unchanged": unchanged_count,
            "errors_count": error_count,
            "errors": errors,
        }
