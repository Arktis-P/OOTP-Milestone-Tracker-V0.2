# Task 006 — Game Milestone Engine

## Goal

Implement the first production milestone engine around already-confirmed per-game OOTP sources.

Order of work:

```text
game_box_*.html
  -> normalized GameRecord / batting & pitching lines
  -> game-level milestone evaluation
  -> log_*.txt only when a rule needs play context
  -> game achievement persistence
```

Do not implement season/career milestone accumulation in this task beyond reusable ledger primitives required by the game parser.

## Required local context

Read first:

- `docs/research/OOTP27_GAME_RECORD_RESEARCH_LOCAL.md`
- `docs/MILESTONE_RULES_DESIGN.md`
- `docs/MILESTONE_ACHIEVEMENT_MODEL.md`
- `docs/OOTP_DATA_IMPORT_PLAN.md`
- `.agents/rules/workflow.md`

The local research already confirmed:

- `game_box_<game_id>.html` identifies game/date/teams/league/player IDs.
- box-score batting additive fields include `AB, R, H, RBI, BB, SO, LOB, HR, SB`.
- box-score pitching additive fields include `outs, H, R, ER, BB, SO, HR, BF, Pitches, W/L/SV/HOLD`.
- `log_<game_id>.txt` maps 1:1 to the game box and exposes stable player IDs plus inning/score/play context.
- `game_id` is suitable for idempotent processing.

Do not require `*_rosters.txt`.

## Architecture

Promote the validated scratch parser into reusable application code. Suggested structure:

```text
src/ootp_milestone_tracker/importer/
├─ game_models.py
├─ game_box_parser.py
├─ play_log_parser.py
├─ competition_classifier.py
└─ game_import_service.py

src/ootp_milestone_tracker/milestones/
├─ game_rules.py
└─ game_evaluator.py
```

Keep parsing, persistence, and rule evaluation separate.

## Normalized models

At minimum define:

```python
GameRecord(
    game_id,
    game_date,
    season,
    competition_type,
    league_id,
    home_team_id,
    away_team_id,
    home_score,
    away_score,
    batting_lines,
    pitching_lines,
)
```

Each batting line must keep `player_id` and all safely extracted per-game additive fields.
Each pitching line must keep `player_id`, `outs`, and all safely extracted per-game additive fields.

For play-context rules expose normalized events such as:

```python
PlayEvent(
    game_id,
    sequence,
    inning,
    half,
    batter_id,
    pitcher_id,
    outs_before,
    score_home,
    score_away,
    result_code,
    text,
    base_state=None,
)
```

Do not fabricate `base_state` if the actual log cannot resolve it reliably.

## Database

Add persistent game-ledger tables sufficient for idempotency and future season/career accumulation.

Recommended minimum:

```text
games
- game_id PK
- game_date
- season
- competition_type
- league_id nullable
- home_team_id
- away_team_id
- home_score
- away_score
- source_hash

player_game_batting
- game_id
- player_id
- team_id nullable
- AB / R / H / RBI / BB / SO / LOB / HR / SB
- PRIMARY KEY(game_id, player_id)

player_game_pitching
- game_id
- player_id
- team_id nullable
- outs / H / R / ER / BB / SO / HR / BF / pitches
- W / L / SV / HOLD
- PRIMARY KEY(game_id, player_id)

game_milestone_achievements
- id
- game_id
- player_id
- competition_type
- rule_key
- title
- achieved_value nullable
- inning nullable
- half nullable
- opponent_player_id nullable
- context_text nullable
- UNIQUE(game_id, player_id, rule_key)
```

The exact schema may differ if the existing DB architecture suggests a cleaner mapping, but game identity and achievement idempotency are mandatory.

## Initial game milestone rules

Implement rules as data/evaluator definitions, not hard-coded UI branches.

### Box-score direct rules

These can be evaluated without detailed play reconstruction.

1. `GAME_HITS_5`
   - batter `H >= 5`

2. `GAME_MULTI_HR`
   - batter `HR >= 2`
   - make threshold configurable later; initial default is 2.

3. `GAME_STRIKEOUTS_10`
   - pitcher `SO >= 10`

### Log-context rules

4. `GAME_GRAND_SLAM`
   - at least one home-run play with bases loaded before the play.
   - implement only if base occupancy can be determined reliably from the real log format.
   - otherwise return/report `UNRESOLVED`, not a guessed achievement.

5. `GAME_CYCLE`
   - same batter records at least one single, double, triple, and home run in the same game.
   - derive hit types from deterministic log result codes/text.
   - do not infer 2B/3B from total H alone.

### Pitching game-completion rules

6. `GAME_SHUTOUT`
   - individual pitcher completes the entire game for his team and allows 0 opponent runs.
   - validate complete-game condition using pitcher outs vs team defensive outs / game length.

7. `GAME_NO_HITTER`
   - individual pitcher completes the entire game and opponent records 0 hits.
   - do not count a combined no-hitter as an individual no-hitter unless a separate rule is later created.

8. `GAME_PERFECT_GAME`
   - individual pitcher completes the entire game and no opposing batter reaches base.
   - requires enough information to exclude H, BB, HBP, errors, catcher interference, etc.
   - if the available sources cannot prove perfection, mark unsupported rather than weakening the definition.

## Important rule semantics

A player may achieve several rules in one game.

Example:

```text
5 H + 2 HR + Cycle
```

must create three independent achievements.

Game milestones are independent of season/career competition totals, but every achievement still stores the game's `competition_type`.

## Configuration readiness

Do not build the full rule editor yet, but define metadata so later UI can expose:

```text
enabled
threshold where numeric
competition types enabled
```

For example `GAME_HITS_5` should later be expressible as a generic `game H >= N` rule.

Special pattern rules (`GRAND_SLAM`, `CYCLE`, `SHUTOUT`, `NO_HITTER`, `PERFECT_GAME`) remain named predicates.

## UI integration

Keep the GUI change small.

Add a game-milestone section/table to the existing Milestones page or a compact filter/tab inside it. Do not add another top-level menu.

Minimum columns:

```text
Date | Player | Competition | Milestone | Opponent/Game | Context
```

Only show context that was actually resolved.

## Validation

Local only. No GitHub Actions / PR / remote push.

Required checks:

1. compileall
2. existing pytest
3. parser tests / sanitized fixtures where useful
4. parse at least 3 real games
5. compare box lines manually to source
6. process same game twice: no duplicate ledger rows or achievements
7. prove direct rules with real or controlled fixtures:
   - 5 hits
   - 2+ HR
   - 10+ SO
8. prove context/special rules where the sample permits
9. explicitly report unsupported/unverifiable special rules
10. GUI smoke for game milestone table

Do not fake a PASS for a milestone whose required source evidence is absent.

## Output report

```text
RESULT: PASS | FAIL

LEDGER
- game parser: PASS/FAIL
- log parser: PASS/FAIL
- DB persistence: PASS/FAIL
- repeated-game idempotency: PASS/FAIL

GAME MILESTONES
- 5 hits: PASS/FAIL/NO SAMPLE
- multi-HR: PASS/FAIL/NO SAMPLE
- grand slam: PASS/FAIL/UNSUPPORTED/NO SAMPLE
- cycle: PASS/FAIL/UNSUPPORTED/NO SAMPLE
- 10 strikeouts: PASS/FAIL/NO SAMPLE
- shutout: PASS/FAIL/UNSUPPORTED/NO SAMPLE
- no-hitter: PASS/FAIL/UNSUPPORTED/NO SAMPLE
- perfect game: PASS/FAIL/UNSUPPORTED/NO SAMPLE

GUI
- game milestone view: PASS/FAIL

FIXES
- NONE or list

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE or exact blockers
```

Suggested local commit:

```text
feat: add game ledger and game milestone engine
```
