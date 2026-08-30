from dataclasses import dataclass
from typing import Optional


@dataclass
class SeasonMilestoneAchievement:
    entity_type: str  # 'player', 'team'
    entity_id: int
    season: int
    competition_type: str
    rule_key: str
    title: str
    achieved_value: float
    threshold_value: Optional[float] = None
    achieved_game_id: Optional[int] = None
    achieved_date: Optional[str] = None
    source: str = "game_crossing"  # 'game_crossing', 'final_export', 'postseason_event'
    context_text: Optional[str] = None
