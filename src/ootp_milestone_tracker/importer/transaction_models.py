from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TransactionParticipant:
    participant_kind: str  # PLAYER / CASH / DRAFT_PICK / OTHER
    display_text: str
    player_id: Optional[int] = None
    from_team_id: Optional[int] = None
    to_team_id: Optional[int] = None
    cash_amount: Optional[int] = None
    role: Optional[str] = None
    sequence: int = 0


@dataclass
class TransactionEventRecord:
    source_family: str
    source_event_id: str
    source_signature: str
    event_key: str
    transaction_type: str  # TRADE / FA_SIGNING / CONTRACT_EXTENSION / ...
    description: str
    event_date: Optional[str] = None
    season: Optional[int] = None
    structured_context_json: Optional[str] = None
    source_ref: Optional[str] = None
    participants: List[TransactionParticipant] = field(default_factory=list)
