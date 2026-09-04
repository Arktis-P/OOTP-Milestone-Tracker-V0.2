from dataclasses import asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.importer.message_models import PlayerHistoryEventRecord
from ootp_milestone_tracker.importer.message_source import discover_messages
from ootp_milestone_tracker.importer.message_parser import (
    parse_injury_message, parse_allstar_message, parse_award_message, parse_monthly_award_message
)
from ootp_milestone_tracker.services.history_renderer import (
    render_manual_league_title_description, translate_league
)

class HistoryService:
    def __init__(self, repository: Repository):
        self.repo = repository

    def scan_and_backfill_history(self, save_dir: Path, incremental_only: bool = False) -> Dict[str, int]:
        min_msg_id = None
        if incremental_only:
            min_msg_id = self.repo.max_scanned_message_id()
            if min_msg_id == 0:
                min_msg_id = None

        scanned_count = 0
        inserted_count = 0
        unresolved_count = 0

        for msg in discover_messages(save_dir, min_msg_id=min_msg_id):
            scanned_count += 1
            events: List[PlayerHistoryEventRecord] = []
            
            # Parse Task 013 event families
            events.extend(parse_injury_message(msg))
            events.extend(parse_allstar_message(msg))
            events.extend(parse_award_message(msg))
            events.extend(parse_monthly_award_message(msg))

            for ev in events:
                if ev.resolution_status == "unresolved":
                    unresolved_count += 1
                rec_dict = asdict(ev)
                self.repo.upsert_player_history_event(rec_dict)
                inserted_count += 1

        return {
            "messages_scanned": scanned_count,
            "events_persisted": inserted_count,
            "unresolved_candidates": unresolved_count
        }

    def add_manual_league_title_award(
        self,
        player_id: int,
        season: int,
        award_key: str,       # 'AVG', 'HR', 'ERA', 'SO', etc.
        stat_value_str: str,  # '.369', '58', '0.98', etc.
        league_label: Optional[str] = None,
        stat_value: Optional[float] = None
    ) -> bool:
        player_info = self.repo.player(player_id)
        team_id = player_info["team_id"] if player_info else None
        league_ko = translate_league(league_label) if league_label else ""

        desc = render_manual_league_title_description(award_key, stat_value_str, league_ko)

        rec = PlayerHistoryEventRecord(
            id=None,
            source_family="MANUAL_USER",
            source_event_id=f"manual_{player_id}_{season}_{award_key}",
            source_signature=f"manual_sig_{player_id}_{season}_{award_key}_{stat_value_str}",
            source_mode="MANUAL_USER",
            event_type="MANUAL_LEAGUE_TITLE",
            event_subtype=f"LEAGUE_TITLE_{award_key}",
            player_id=player_id,
            team_id=team_id,
            league_id=None,
            league_label=league_label,
            season=season,
            event_date=f"{season}-11-01",
            position_label=None,
            title=desc,
            context_text=f"수동 입력 리그 타이틀 ({award_key}: {stat_value_str})",
            structured_context_json=None,
            resolution_status="published",
            source_ref="manual_user_input"
        )
        return self.repo.upsert_player_history_event(asdict(rec))

    def get_history_events(self, tracked_only: bool = False, event_type: str = "", search: str = "") -> List[Dict[str, Any]]:
        return self.repo.history_events(tracked_only=tracked_only, event_type=event_type, search=search)
