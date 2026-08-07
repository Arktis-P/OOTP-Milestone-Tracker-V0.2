"""
Manual Event & Player Repository (Phase 8.1 & 8.2)
Handles user-entered manual events, awards, trades, injuries, and temporary player registration.
"""

import sqlite3
import datetime
from typing import Dict, Any, Optional
from core.db.player_repo import PlayerRepository


class ManualEventRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.player_repo = PlayerRepository(conn)

    def add_manual_event(
        self,
        event_type: str,
        first_name: str,
        last_name: str,
        season: int,
        event_date: str,
        title: str,
        description: str = "",
        ootp_player_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Creates or reuses player, and records manual event."""
        p = self.player_repo.get_or_create_player(ootp_player_id, first_name, last_name)
        p_id = p["id"]
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO manual_events (event_type, player_id, team_id, season, event_date, title, description, source, created_at)
               VALUES (?, ?, NULL, ?, ?, ?, ?, 'manual', ?)""",
            (event_type, p_id, season, event_date, title, description, now_iso)
        )
        evt_id = cursor.lastrowid

        # Also write into milestone_events as manual source for unified viewing
        cursor.execute(
            """INSERT INTO milestone_events
               (policy_key, player_id, team_id, season, game_id, event_date, scope, category, grade, value, threshold, source_type, source_ref, created_at)
               VALUES (?, ?, NULL, ?, NULL, ?, 'manual', 'manual', 'rare', 1.0, 1.0, 'manual', ?, ?)""",
            (f"manual_{event_type}", p_id, season, event_date, str(evt_id), now_iso)
        )

        self.conn.commit()
        return {
            "id": evt_id,
            "player_id": p_id,
            "display_name": p["display_name"],
            "event_type": event_type,
            "title": title,
            "event_date": event_date,
        }
