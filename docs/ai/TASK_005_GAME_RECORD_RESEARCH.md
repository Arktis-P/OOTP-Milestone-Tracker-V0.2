# Task 005 — OOTP Game Record Deep Research

## Goal

Before implementing the real importer, determine exactly how OOTP 27 per-game files can drive an incremental local stat ledger.

The intended production model is:

```text
manual player_*_stats baseline
  + automatically created game records after baseline
  -> internal DB current totals
```

Do not implement the full importer yet. This task is source research plus a small read-only prototype parser only when needed to prove field extraction.

## Source priority for this task

1. `news/html/box_scores/game_box_*.html`
   - authoritative per-game player stat deltas
   - game metadata
2. `news/txt/leagues/log_*.txt`
   - exact play-by-play context
3. `messages/message*.txt`
   - optional corroboration only
4. `import_export/player_*_stats.txt`
   - baseline/checkpoint reference only

Do not require `*_rosters.txt`.

## Required questions to answer

### A. Game identity

For representative game-box files confirm:

- game ID from filename
- whether the same game ID appears inside HTML
- in-game date
- season/year
- league/tournament ID if present
- home team ID and away team ID
- final score
- completed/cancelled/suspended status if represented

### B. Competition classification

Determine a reliable way to classify every game into exactly one canonical type:

```text
regular_season
postseason
spring_training
international
```

Record the exact discriminator. Prefer explicit fields/IDs over date heuristics.

If classification needs a mapping from league/tournament IDs, document the mapping source.

Do not guess ambiguous games.

### C. Player game lines

For at least one batter and one pitcher confirm whether `game_box_*.html` exposes stable `player_id` links and the exact per-game fields.

Batting priority:
- G/appearance signal
- PA
- AB
- H
- 2B
- 3B
- HR
- RBI
- BB
- SO
- SB
- CS when available
- HBP/SF when available

Pitching priority:
- G/appearance signal
- GS
- W/L/SV decision if represented
- IP or outs recorded
- H
- R/ER
- BB
- SO
- HR allowed when available

Identify which values can be safely summed into season/career totals and which are derived rates.

### D. Player game count

Confirm how to derive player game number.

Preferred rule:

```text
count distinct processed games in which player appeared
within same competition_type
```

For season milestone:

```text
player_id + season + competition_type
```

For career milestone:

```text
player_id + competition_type
```

Check whether game-box participation is sufficient for this.

### E. Play-by-play linkage

For `log_*.txt` confirm:

- how its game ID maps to `game_box_<game_id>.html`
- inning and top/bottom
- batter player ID
- pitcher player ID
- outs before/after play if available
- base state if available
- score before/after play if available
- play result text
- whether hit/home-run/strikeout/win-save related milestone plays can be identified deterministically

The milestone engine should not infer opponent player from names if stable IDs are available.

### F. File lifecycle

Determine:

- whether a new game box/log file appears after every completed game
- whether old files normally remain unchanged
- whether timestamps are trustworthy enough for discovery
- whether filename/game ID uniqueness is enough for idempotency
- any evidence of rewritten files after resim/reload/correction

If files can change, recommend hash-based change detection.

### G. Baseline handoff

The app will sometimes receive a manually generated `player_*_stats.txt` baseline before a season or at another checkpoint.

Research how to prevent double-counting games already represented by that baseline.

Preferred general design:

```text
baseline created
-> record the set/max identity of game files already present at baseline time
-> only games not included in that checkpoint contribute incremental deltas
```

Do not rely only on filesystem modified time if game IDs provide a safer boundary.

## Required sample coverage

Inspect representative files for as many contexts as actually exist in the save:

- regular season: REQUIRED
- postseason: inspect if available
- spring training: inspect if available
- international: inspect if available

If a context is absent, report `NOT AVAILABLE IN SAMPLE`; do not fabricate conclusions.

## Output

Update/create:

```text
docs/research/OOTP27_GAME_RECORD_RESEARCH_LOCAL.md
```

Required sections:

1. Game-box schema/field map
2. Log schema/link map
3. Competition-type classifier
4. Game-player delta map
5. Game-count derivation
6. Game-box ↔ log linkage
7. File lifecycle/idempotency
8. Baseline cutoff strategy
9. Known ambiguities/blockers
10. Recommended parser API

Recommended parser API shape:

```python
GameRecord(
    game_id,
    game_date,
    season,
    competition_type,
    home_team_id,
    away_team_id,
    status,
    batting_lines,
    pitching_lines,
)
```

and optionally:

```python
PlayEvent(
    game_id,
    sequence,
    inning,
    half,
    batter_id,
    pitcher_id,
    outs,
    base_state,
    score_home,
    score_away,
    result,
    text,
)
```

## Validation

Local only. No Actions/PR/push.

Run:

```powershell
.\.venv\Scripts\python.exe -m compileall -q src scripts
.\.venv\Scripts\python.exe -m pytest -q
```

If a small research parser/script is added, validate it against at least 3 actual games and manually compare extracted values against the HTML/log contents.

## Scope limits

Do NOT:

- build the final SQLite importer
- rewrite the GUI
- implement milestone settings UI
- implement forecasts
- modify OOTP save files
- commit raw save/game files
- use roster exports

## Git policy

If only the research report changes, create one local commit.
If a tiny reusable parser prototype is needed, include it in the same final local commit after validation.
Do not push.

Suggested commit:

```text
research: map OOTP game records for incremental tracking
```

## Report format

```text
RESULT: PASS | FAIL

GAME BOX
- game id: PASS/FAIL
- game date: PASS/FAIL
- teams: PASS/FAIL
- player IDs: PASS/FAIL
- batting deltas: PASS/FAIL
- pitching deltas: PASS/FAIL

LOG
- box/log game linkage: PASS/FAIL
- batter/pitcher IDs: PASS/FAIL
- inning/score/context: PASS/FAIL

COMPETITION TYPES
- regular season: CONFIRMED/UNKNOWN
- postseason: CONFIRMED/NOT AVAILABLE/UNKNOWN
- spring training: CONFIRMED/NOT AVAILABLE/UNKNOWN
- international: CONFIRMED/NOT AVAILABLE/UNKNOWN

LEDGER
- player game-count derivation: PASS/FAIL
- idempotent game identity: PASS/FAIL
- baseline cutoff strategy: PASS/FAIL

FILES
- docs/research/OOTP27_GAME_RECORD_RESEARCH_LOCAL.md

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE
or
- <exact blocker>
```
