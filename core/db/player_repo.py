"""
Player Repository & Identity Merge System
Implements OOTP player identity resolution, temporary player creation, and safe merging.
"""

import sqlite3
import datetime
from typing import Optional, Dict, Any, List


class PlayerRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_or_create_player(
        self,
        ootp_player_id: Optional[int],
        first_name: str,
        last_name: str,
        display_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Looks up player by ootp_player_id if provided; creates confirmed or temporary player otherwise."""
        cursor = self.conn.cursor()
        disp_name = display_name or f"{first_name} {last_name}".strip()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if ootp_player_id is not None:
            cursor.execute("SELECT * FROM players WHERE ootp_player_id = ?", (ootp_player_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)

            cursor.execute(
                """INSERT INTO players (ootp_player_id, first_name, last_name, display_name, is_temporary, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 0, ?, ?)""",
                (ootp_player_id, first_name, last_name, disp_name, now_iso, now_iso)
            )
            player_id = cursor.lastrowid
            self.conn.commit()
            return {
                "id": player_id,
                "ootp_player_id": ootp_player_id,
                "first_name": first_name,
                "last_name": last_name,
                "display_name": disp_name,
                "is_temporary": 0,
                "created_at": now_iso,
                "updated_at": now_iso
            }

        # Create temporary player
        cursor.execute(
            """INSERT INTO players (ootp_player_id, first_name, last_name, display_name, is_temporary, created_at, updated_at)
               VALUES (NULL, ?, ?, ?, 1, ?, ?)""",
            (first_name, last_name, disp_name, now_iso, now_iso)
        )
        player_id = cursor.lastrowid
        self.conn.commit()
        return {
            "id": player_id,
            "ootp_player_id": None,
            "first_name": first_name,
            "last_name": last_name,
            "display_name": disp_name,
            "is_temporary": 1,
            "created_at": now_iso,
            "updated_at": now_iso
        }

    def merge_temporary_player(self, temp_player_id: int, target_player_id: int) -> bool:
        """
        Merges temporary player into target confirmed player in a single transaction.
        Re-links milestone events, manual events, stats, affiliations, streaks, and deletes temporary player.
        """
        if temp_player_id == target_player_id:
            return False

        cursor = self.conn.cursor()
        try:
            self.conn.execute("BEGIN TRANSACTION;")

            # Re-link milestone_events
            cursor.execute("UPDATE milestone_events SET player_id = ? WHERE player_id = ?", (target_player_id, temp_player_id))

            # Re-link manual_events
            cursor.execute("UPDATE manual_events SET player_id = ? WHERE player_id = ?", (target_player_id, temp_player_id))

            # Re-link affiliations
            cursor.execute("UPDATE player_team_affiliations SET player_id = ? WHERE player_id = ?", (target_player_id, temp_player_id))

            # Re-link batting_game_stats (ignore duplicates if target already has stats for game)
            cursor.execute("UPDATE OR IGNORE batting_game_stats SET player_id = ? WHERE player_id = ?", (target_player_id, temp_player_id))
            cursor.execute("DELETE FROM batting_game_stats WHERE player_id = ?", (temp_player_id,))

            # Re-link pitching_game_stats
            cursor.execute("UPDATE OR IGNORE pitching_game_stats SET player_id = ? WHERE player_id = ?", (target_player_id, temp_player_id))
            cursor.execute("DELETE FROM pitching_game_stats WHERE player_id = ?", (temp_player_id,))

            # Re-link streak_states & streak_events where subject_type = 'player'
            cursor.execute("UPDATE OR IGNORE streak_states SET subject_id = ? WHERE subject_type = 'player' AND subject_id = ?", (target_player_id, temp_player_id))
            cursor.execute("DELETE FROM streak_states WHERE subject_type = 'player' AND subject_id = ?", (temp_player_id,))

            cursor.execute("UPDATE streak_events SET subject_id = ? WHERE subject_type = 'player' AND subject_id = ?", (target_player_id, temp_player_id))

            # Delete temporary player
            cursor.execute("DELETE FROM players WHERE id = ? AND is_temporary = 1", (temp_player_id,))

            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            raise
