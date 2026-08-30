# Task 006 — Game Milestone Engine

## Goal

Implement the first production milestone engine around already-confirmed per-game OOTP sources.

Before implementing milestone rules, **re-verify the batting source semantics inside `game_box_*.html`**. The upper batting table and the lower textual batting-summary area do not necessarily represent the same scope.

The user has confirmed that event/counting data such as home runs, stolen bases, doubles, and triples must be read from the lower textual batting-summary area, where OOTP exposes the current-game occurrence count and season total, and for home runs may also include pitcher/context details.

Do not treat a season-total value displayed in the upper table as a per-game delta.

Order of work:

```text
game_box_*.html
  -> verify upper-table vs lower-text semantics
  -> normalized GameRecord / batting & pitching lines
  -> game-level milestone evaluation
  -> log_*.txt only when additional play context is needed
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

The previous local research confirmed:

- `game_box_<game_id>.html` identifies game/date/teams/league/player IDs.
- the upper batting table contains useful per-game line information, but **some displayed fields may be season totals and must not be assumed to be game deltas**.
- the lower batting-summary text contains event/count data such as `2B`, `3B`, `HR`, `SB` and may include both the number in this game and the resulting season total.
- home-run summary text may also include the opposing pitcher and contextual information.
- box-score pitching additive fields include `outs, H, R, ER, BB, SO, HR, BF, Pitches, W/L/SV/HOLD` where locally verified.
- `log_<game_id>.txt` maps 1:1 to the game box and exposes stable player IDs plus inning/score/play context.
- `game_id` is suitable for idempotent processing.

Do not require `*_rosters.txt`.

## Mandatory batting-source verification

This verification happens **before production parser implementation**.

Inspect multiple actual `game_box_*.html` files and document the exact HTML/text patterns for the lower batting-summary section.

At minimum verify:

```text
Doubles / 2B
Triples / 3B
Home Runs / HR
Stolen Bases / SB
```

For each category determine:

1. how the player is identified,
2. how many occurred **in this game**,
3. how the resulting **season total** is represented,
4. whether multiple events by the same player are represented separately or compacted,
5. whether opponent-player information is included,
6. whether inning / score / runners / outs or other context is included,
7. whether the text format changes when several players record the same event.

For home runs specifically verify whether the summary can reliably extract:

```text
batter_id
pitcher_id if linked
home_runs_this_game
season_home_run_number
inning/context if present
text description
```

For stolen bases verify whether the summary can reliably extract:

```text
runner/player_id
stolen_bases_this_game
season_stolen_base_number
base stolen if represented
pitcher/catcher or context if represented
```

For doubles/triples verify whether the summary exposes both game occurrence(s) and season ordinal/total.

### Source-of-truth rule

For `2B`, `3B`, `HR`, and `SB`:

**Use the lower textual batting-summary area as the authoritative per-game source unless actual local inspection proves a safer equivalent source.**

Do not obtain these values by subtracting season totals between files.

Do not use a season-total field from the upper batting table as a game delta.

If a prior research/prototype parser currently reads these stats from the wrong section, correct the production parser and update the research notes.

### Cross-check upper table

Also re-check the upper batting table field-by-field.

For every column intended for the game ledger, explicitly classify it as one of:

```text
GAME_DELTA
SEASON_TOTAL
DERIVED_RATE
UNKNOWN
```

Examples of fields to verify rather than assume:

```text
AB
R
H
RBI
BB
SO
LOB
AVG
HR if displayed
SB if displayed
```

Only `GAME_DELTA` values may be written directly into `player_game_batting`.

`SEASON_TOTAL` values may be retained as optional reconciliation metadata, but must not be added to the ledger.

`DERIVED_RATE` values such as AVG are never additive.

If a field is ambiguous, classify it `UNKNOWN` and do not use it for production aggregation until resolved.

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

The game-box parser may internally separate:

```text
parse_game_header()
parse_batting_table()
parse_batting_summary_text()
parse_pitching_table()
```

This is preferred over mixing the lower textual-event grammar with table-column parsing.

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
    batting_events,
)
```

Each batting line must keep `player_id` and only safely extracted **per-game** fields.

Recommended game batting line fields after verification:

```text
AB / R / H / RBI / BB / SO / LOB
2B / 3B / HR / SB
```

but every field must come from the correct source region as established above.

Each pitching line must keep `player_id`, `outs`, and all safely extracted per-game additive fields.

Preserve normalized lower-summary events where useful, for example:

```python
BattingEvent(
    game_id,
    player_id,
    event_type,          # DOUBLE / TRIPLE / HOME_RUN / STOLEN_BASE
    game_occurrence,
    season_total=None,
    opponent_player_id=None,
    context_text=None,
)
```

If one text entry represents multiple same-game events, either emit multiple normalized events or store an explicit `game_count`; choose one representation and test it.

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
- AB / R / H / RBI / BB / SO / LOB
- doubles
- triples
- HR
- SB
- PRIMARY KEY(game_id, player_id)

player_game_pitching
- game_id
- player_id
- team_id nullable
- outs / H / R / ER / BB / SO / HR / BF / pitches
- W / L / SV / HOLD
- PRIMARY KEY(game_id, player_id)

game_batting_events
- game_id
- player_id
- sequence_or_index
- event_type
- season_total nullable
- opponent_player_id nullable
- context_text nullable
- PRIMARY KEY or UNIQUE sufficient for idempotency

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

Do not duplicate a home run or stolen base merely because the same event is represented both in the lower summary and play log. The lower summary is the box-score event/count source; the log is contextual evidence.

## Initial game milestone rules

Implement rules as data/evaluator definitions, not hard-coded UI branches.

### Direct per-game numeric rules

1. `GAME_HITS_5`
   - batter `H >= 5`
   - use a value verified as a real game delta.

2. `GAME_MULTI_HR`
   - batter `HR >= 2`
   - **HR must come from the verified lower batting-summary parsing, not an upper-table season total.**
   - make threshold configurable later; initial default is 2.

3. `GAME_STRIKEOUTS_10`
   - pitcher `SO >= 10`

### Batting-event pattern rules

4. `GAME_GRAND_SLAM`
   - at least one home-run play with bases loaded before the play.
   - the lower HR summary may provide useful pitcher/context metadata and should be preserved.
   - use `log_*.txt` to prove bases loaded unless the lower summary itself deterministically supplies equivalent evidence.
   - otherwise return/report `UNRESOLVED`, not a guessed achievement.

5. `GAME_CYCLE`
   - same batter records at least one single, double, triple, and home run in the same game.
   - doubles/triples/home runs should use the verified lower batting-summary source when available.
   - derive singles as `H - doubles - triples - HR` only if `H` is verified as a per-game hit total and all extra-base hit counts are complete/reliable; otherwise derive hit types from deterministic play events.
   - require every component to be proven. Do not infer 2B/3B from total H alone.

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

The lower batting summary may expose the resulting season ordinal, e.g. a player's season HR number. Preserve that metadata where useful, but **do not let season-total metadata replace the game-count field**.

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

For HR-related achievements, if the lower summary reliably supplies season HR number and opponent pitcher/context, preserve those fields so a later detail view can display them.

## Validation

Local only. No GitHub Actions / PR / remote push.

Required checks:

1. compileall
2. existing pytest
3. parser tests / sanitized fixtures where useful
4. parse at least 3 real games
5. manually compare upper batting-table values and lower batting-summary text against source
6. explicitly verify `2B`, `3B`, `HR`, `SB` extraction from the lower textual section
7. verify same-game count and season-total interpretation for each available event type
8. for at least one HR sample, verify batter ID, season HR ordinal/total, and pitcher/context when present
9. process same game twice: no duplicate ledger rows/events/achievements
10. prove direct rules with real or controlled fixtures:
   - 5 hits
   - 2+ HR using lower-summary HR count
   - 10+ SO
11. prove context/special rules where the sample permits
12. explicitly report unsupported/unverifiable special rules
13. GUI smoke for game milestone table

Do not fake a PASS for a milestone whose required source evidence is absent.

## Required source-semantics report

Before reporting Task 006 PASS, include a compact mapping table in the local research/report output:

```text
FIELD | SOURCE REGION | SEMANTICS | USED AS GAME DELTA?
AB    | upper table   | ...       | YES/NO
H     | upper table   | ...       | YES/NO
RBI   | upper table   | ...       | YES/NO
2B    | lower text    | game + season total | YES
3B    | lower text    | game + season total | YES
HR    | lower text    | game + season total + context | YES
SB    | lower text    | game + season total | YES
```

The actual result must come from local inspection; the example row semantics above are not permission to assume an unverified upper-table field.

Update `docs/research/OOTP27_GAME_RECORD_RESEARCH_LOCAL.md` if the previous research incorrectly classified any batting field.

## Output report

```text
RESULT: PASS | FAIL

SOURCE SEMANTICS
- upper batting table classified: PASS/FAIL
- lower batting summary identified: PASS/FAIL
- doubles from lower text: PASS/FAIL/NO SAMPLE
- triples from lower text: PASS/FAIL/NO SAMPLE
- home runs from lower text: PASS/FAIL/NO SAMPLE
- stolen bases from lower text: PASS/FAIL/NO SAMPLE
- HR pitcher/context: PASS/FAIL/NO SAMPLE

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

FIELD MAPPING NOTES
- <only corrected/important source semantics>

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
