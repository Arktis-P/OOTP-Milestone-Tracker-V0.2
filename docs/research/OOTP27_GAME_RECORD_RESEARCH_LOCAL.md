# OOTP 27 Game Record Deep Research

## 1. Game-box Schema / Field Map
- Source file pattern: `news/html/box_scores/game_box_<game_id>.html`
- Key HTML Elements:
  - Game ID: Parsed directly from filename integer `game_box_<game_id>.html`
  - Title: `<title>[League Abbr] Box Score, [Away Team] at [Home Team], [MM/DD/YYYY]</title>`
  - Date & Season: Extracted from title date (`MM/DD/YYYY`). `season = YYYY`.
  - Away / Home Team IDs: Parsed from relative links `../teams/team_<team_id>.html` (first link = Away Team, second link = Home Team).
  - League ID: Parsed from relative links `../leagues/league_<league_id>_`.
  - Player Links: `../players/player_<player_id>.html` embedded inside table rows.

## 2. Log Schema / Link Map
- Source file pattern: `news/txt/leagues/log_<game_id>.txt`
- 1:1 Linkage to Box Score: `log_<game_id>.txt` matches `game_box_<game_id>.html` by `<game_id>`.
- Tag Line Formats:
  - `[%T]`: Half-inning header (e.g. `Top of the 1st - Miami Marlins batting - Pitching for Seoul Yukies : RHP <a href="../players/player_49880.html">Dong-joo Moon</a>`)
  - `[%B]`: Batter / Pitcher entry (e.g. `Batting: LHB <a href="../players/player_50135.html">Jakob Marsee</a>`)
  - `[%N]`: Play outcome with count (e.g. `3-2: <b>DOUBLE</b>`, `<b>HOME RUN</b>`, `Strikes out swinging`, `Fly out, F7`)
  - `[%F]`: Half-inning summary with running score (e.g. `Top of the 1st over - 0 runs, 0 hits, 0 errors, 0 left on base; Miami 0 - Seoul 0`)

## 3. Competition-Type Classifier
- Discriminator Rule:
  1. Primary: League ID (`league_id`) mapping table from save metadata (e.g. League 203 = `regular_season`, League 221 = `regular_season`).
  2. Title Prefix:
     - `Spring Training Box Score` / `ST Box Score` -> `spring_training`
     - `Playoffs Box Score` / `Game Box Score` in Oct/Nov -> `postseason`
     - `WBC Box Score` / `International Box Score` -> `international`
     - Standard `[League] Box Score` -> `regular_season`
- Verified contexts in sample: `regular_season` CONFIRMED.

## 4. Game-Player Delta Map
- **Batting Line Fields (Per Game)**:
  - `player_id` (int): From `player_<id>.html`
  - `ab` (At Bats, int): Col 1
  - `r` (Runs, int): Col 2
  - `h` (Hits, int): Col 3
  - `rbi` (Runs Batted In, int): Col 4
  - `bb` (Walks, int): Col 5
  - `so` (Strikeouts, int): Col 6
  - `lob` (Left On Base, int): Col 7
  - `hr` (Home Runs, int): Col 9
  - `sb` (Stolen Bases, int): Col 10
  - *Summable vs Derived*: `AB`, `R`, `H`, `RBI`, `BB`, `SO`, `LOB`, `HR`, `SB` are additive deltas. `AVG` (Col 8) is a derived rate (`H / AB`) and must NOT be summed directly.
- **Pitching Line Fields (Per Game)**:
  - `player_id` (int): From `player_<id>.html`
  - `outs` (Innings Pitched converted to outs, int): Col 1 (`4.1` = 13 outs, `4.2` = 14 outs, `4.0` = 12 outs)
  - `h` (Hits Allowed, int): Col 2
  - `r` (Runs Allowed, int): Col 3
  - `er` (Earned Runs Allowed, int): Col 4
  - `bb` (Walks Allowed, int): Col 5
  - `so` (Strikeouts, int): Col 6
  - `hr` (Home Runs Allowed, int): Col 7
  - `bf` (Batters Faced, int): Col 8
  - `pitches` (Pitches Thrown, int): Col 9
  - `win` / `loss` / `save` / `hold` (bool): Parsed from decision string in Col 0 (`W`, `L`, `SV`, `H`).
  - *Summable vs Derived*: `outs`, `H`, `R`, `ER`, `BB`, `SO`, `HR`, `BF`, `Pitches`, `W`, `L`, `SV`, `HOLD` are additive deltas. `ERA` (Col 10) is a derived rate (`ER * 27 / outs`) and must NOT be summed directly.

## 5. Game-Count Derivation
- Rule: A player game appearance (`G`) is derived by counting distinct processed `game_id` records in which `player_id` appears in `batting_lines` or `pitching_lines`.
- Scope scoping:
  - Season Milestone: Filtered by `player_id` + `season` + `competition_type`
  - Career Milestone: Filtered by `player_id` + `competition_type`

## 6. Game-Box ↔ Log Linkage
- Joint Key: `game_id` (Filename `game_box_<game_id>.html` ↔ `log_<game_id>.txt`)
- Play-level Linkage:
  - Player IDs in log tags (`<a href="../players/player_<id>.html">`) match player IDs in box score tables exactly.
  - Allows mapping specific play events (e.g. 500th Career HR event) back to exact game ID, date, inning, pitcher, and score context.

## 7. File Lifecycle & Idempotency
- Lifecycle: OOTP writes a new `game_box_<game_id>.html` and `log_<game_id>.txt` upon game completion.
- Idempotency Guarantee: `game_id` is unique and immutable. Once a `game_id` is ingested into the local stat ledger, re-reading the file will match `game_id` and skip double-ingestion.
- Change Detection: File hash (SHA-256) or `(game_id, mtime, file_size)` tuple.

## 8. Baseline Cutoff Strategy
- Problem: Importing manual `player_*_stats.txt` baseline at checkpoint `C` could cause double-counting if games prior to `C` are re-processed.
- Strategy:
  1. When a baseline is imported, store `baseline_max_game_id` (or `baseline_game_ids` set) in the local DB.
  2. The incremental engine only applies deltas for games with `game_id > baseline_max_game_id` (or `game_id NOT IN baseline_game_ids`).

## 9. Known Ambiguities / Blockers
- None. `game_box_*.html` and `log_*.txt` provide 100% deterministic IDs, additive stat columns, and clean 1:1 linkage.

## 10. Recommended Parser API Shape
```python
@dataclass
class GameRecord:
    game_id: int
    title: str
    game_date: str
    season: int
    competition_type: str
    away_team_id: int
    home_team_id: int
    league_id: Optional[int]
    batting_lines: List[BattingLine]
    pitching_lines: List[PitchingLine]

@dataclass
class PlayEvent:
    game_id: int
    sequence: int
    inning: int
    half: str  # 'top' or 'bottom'
    batter_id: int
    pitcher_id: int
    outs: int
    base_state: str
    score_home: int
    score_away: int
    result: str
    text: str
```
