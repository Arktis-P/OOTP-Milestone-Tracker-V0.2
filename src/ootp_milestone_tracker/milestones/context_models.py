import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


@dataclass
class AchievementContext:
    resolution_status: str = "game_resolved"  # 'play_resolved', 'game_resolved', 'final_export', 'partial'
    game_id: Optional[int] = None
    game_date: Optional[str] = None
    inning: Optional[int] = None
    half: Optional[str] = None  # 'top'/'bottom' or '초'/'말'
    outs_before: Optional[int] = None
    base_state_before: Optional[str] = None  # '1루', '1,2루', '2,3루', '만루'
    score_before_home: Optional[int] = None
    score_before_away: Optional[int] = None
    score_after_home: Optional[int] = None
    score_after_away: Optional[int] = None
    opponent_team_id: Optional[int] = None
    opponent_team_name: Optional[str] = None
    opponent_player_id: Optional[int] = None
    opponent_player_name: Optional[str] = None
    play_result: Optional[str] = None
    pitch_count: Optional[int] = None
    pitch_sequence: Optional[str] = None
    batter_name: Optional[str] = None
    rbi_count: Optional[int] = None
    runs_count: Optional[int] = None
    destination_base: Optional[str] = None  # '2루', '3루', '홈'
    lineup_names: List[str] = field(default_factory=list)
    game_line_summary: Optional[str] = None
    raw_context: Optional[str] = None

    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict) -> "AchievementContext":
        if not data:
            return cls()
        known_keys = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in known_keys}
        return cls(**filtered)

    @classmethod
    def from_json(cls, json_str: Optional[str]) -> "AchievementContext":
        if not json_str:
            return cls()
        try:
            return cls.from_dict(json.loads(json_str))
        except Exception:
            return cls()
