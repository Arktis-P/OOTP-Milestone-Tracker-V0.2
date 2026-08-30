from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BattingLine:
    player_id: int
    name: str
    team_id: Optional[int]
    ab: int = 0
    r: int = 0
    h: int = 0
    rbi: int = 0
    bb: int = 0
    so: int = 0
    lob: int = 0
    doubles: int = 0
    triples: int = 0
    hr: int = 0
    sb: int = 0
    is_starter: bool = True



@dataclass
class PitchingLine:
    player_id: int
    name: str
    team_id: Optional[int]
    outs: int = 0
    h: int = 0
    r: int = 0
    er: int = 0
    bb: int = 0
    so: int = 0
    hr: int = 0
    bf: int = 0
    pitches: int = 0
    win: bool = False
    loss: bool = False
    save: bool = False
    hold: bool = False


@dataclass
class BattingEvent:
    game_id: int
    player_id: int
    event_index: int
    event_type: str  # DOUBLE, TRIPLE, HOME_RUN, STOLEN_BASE
    season_total: Optional[int] = None
    opponent_player_id: Optional[int] = None
    context_text: Optional[str] = None


@dataclass
class PlayEvent:
    game_id: int
    sequence: int
    inning: int
    half: str  # top, bottom
    batter_id: int
    pitcher_id: int
    outs_before: int
    score_home: int
    score_away: int
    result_code: str  # HR, 2B, 3B, 1B, K, etc.
    text: str
    base_state: Optional[str] = None  # e.g., '100', '111' if deterministically known


@dataclass
class GameRecord:
    game_id: int
    title: str
    game_date: str
    season: int
    competition_type: str
    away_team_id: int
    home_team_id: int
    league_id: Optional[int] = None
    away_score: int = 0

    home_score: int = 0
    source_hash: str = ""
    batting_lines: List[BattingLine] = field(default_factory=list)
    pitching_lines: List[PitchingLine] = field(default_factory=list)
    batting_events: List[BattingEvent] = field(default_factory=list)
