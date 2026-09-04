import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional, Dict, Any

@dataclass
class RawMessage:
    msg_id: int
    filename: str
    filepath: str
    raw_text: str
    first_line: str
    signature: str
    players: List[Tuple[str, int]] = field(default_factory=list)  # (name, player_id)
    teams: List[Tuple[str, int]] = field(default_factory=list)    # (name, team_id)

    @classmethod
    def create(cls, msg_id: int, filename: str, filepath: str, raw_text: str,
               players: List[Tuple[str, int]], teams: List[Tuple[str, int]]) -> "RawMessage":
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        first_line = lines[0] if lines else ""
        sig = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()
        return cls(
            msg_id=msg_id,
            filename=filename,
            filepath=filepath,
            raw_text=raw_text,
            first_line=first_line,
            signature=sig,
            players=players,
            teams=teams
        )

@dataclass
class PlayerHistoryEventRecord:
    id: Optional[int]
    source_family: str           # e.g. 'MESSAGES', 'MANUAL_USER'
    source_event_id: str         # e.g. 'msg_7760', 'manual_45705_2026_AVG'
    source_signature: str        # sha256 or unique token
    source_mode: str             # 'AUTOMATIC_MESSAGE', 'MANUAL_USER'
    event_type: str              # 'INJURY', 'ALL_STAR', 'AWARD', 'MONTHLY_AWARD', 'MANUAL_LEAGUE_TITLE'
    event_subtype: str           # e.g. 'INJURY_OCCURRENCE', 'ALL_STAR_STARTER', 'MVP', 'AVG'
    player_id: int
    team_id: Optional[int] = None
    league_id: Optional[int] = None
    league_label: Optional[str] = None
    season: Optional[int] = None
    event_date: Optional[str] = None
    position_label: Optional[str] = None
    title: str = ""
    context_text: Optional[str] = None
    structured_context_json: Optional[str] = None
    resolution_status: str = "published"  # 'published' or 'unresolved'
    source_ref: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
