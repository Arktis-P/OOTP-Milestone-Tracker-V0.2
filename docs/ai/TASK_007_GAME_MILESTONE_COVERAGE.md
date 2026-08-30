# Task 007 — Game Milestone Coverage & Verification

## Goal

Verify and extend the completed game-ledger / game-milestone engine so that every game milestone requested by the project is represented correctly in code, persisted correctly, and tested against both real OOTP save data and controlled fixtures.

This task starts from the local feature commit reported as:

```text
d3cd79f feat: add game ledger and game milestone engine
```

Do not discard that local commit when syncing with `origin/user/Workspace`.

Read first:

- `docs/GAME_MILESTONE_CATALOG.md`
- `docs/research/OOTP27_GAME_RECORD_RESEARCH_LOCAL.md`
- `docs/ai/TASK_006_GAME_MILESTONE_ENGINE.md`
- relevant game parser/evaluator/tests added by the local Task 006 commit

## Critical conclusion before coding

The Task 006 report proves only the currently implemented eight rules:

- 5 hits
- 2+ HR
- 10 SO
- grand slam
- cycle
- shutout
- no-hitter/no-hit result
- perfect game

It does NOT by itself prove complete coverage for the project catalog below. Perform an explicit code-to-requirement coverage audit before changing code.

## Canonical requested catalog

### Batter

Threshold families:

```text
Hits: 4 / 5 / 6 / 7
RBI: 5 / 6 / 7 / 8 / 9 / 10
HR: 2 / 3 / 4 / 5
SB: 3 / 4 / 5 / 6 / 7
```

Named rules:

```text
Grand Slam
Cycle
```

### Pitcher

Threshold family:

```text
SO: 10 / 15 / 20 / 25 / 30
```

Named hierarchy:

```text
Complete-game win
Shutout win
No-hit no-run
Perfect game
```

### Team

```text
Starting lineup all hit
All appearing batters hit
Starting lineup all RBI
All appearing batters RBI
Team shutout win
Team no-hit no-run
Team perfect game
```

If the product/UI later chooses to combine or hide starter/all-appearance variants, keep the evaluator semantics distinct so the data model remains unambiguous.

## Highest-only semantics — mandatory

Within one threshold family, persist ONLY the highest configured threshold reached in that game.

Required boundary examples:

```text
H=3  -> none
H=4  -> H4
H=5  -> H5 only (NOT H4)
H=7  -> H7 only
H=8  -> H7 only, achieved_value=8

RBI=4  -> none
RBI=5  -> RBI5
RBI=8  -> RBI8 only
RBI=11 -> RBI10 only, achieved_value=11

HR=1 -> none
HR=2 -> HR2
HR=4 -> HR4 only
HR=6 -> HR5 only, achieved_value=6

SB=2 -> none
SB=3 -> SB3
SB=7 -> SB7 only
SB=8 -> SB7 only, achieved_value=8

SO=9  -> none
SO=10 -> SO10
SO=14 -> SO10
SO=15 -> SO15 only
SO=17 -> SO15 only
SO=25 -> SO25 only
SO=31 -> SO30 only, achieved_value=31
```

Do not create multiple lower achievements in any of these cases.

### Nested pitching hierarchy

For the same pitcher/game:

```text
PERFECT_GAME > NO_HIT_NO_RUN > SHUTOUT_WIN > COMPLETE_GAME_WIN
```

Persist only the highest satisfied special pitching result.

Examples:

- perfect game -> only `GAME_PERFECT_GAME`; do not additionally store no-hit-no-run, shutout, complete-game win.
- no-hit-no-run but not perfect -> only `GAME_NO_HIT_NO_RUN`.
- shutout but allowed hits -> only `GAME_SHUTOUT_WIN`.
- complete-game win with runs allowed -> only `GAME_COMPLETE_GAME_WIN`.

Independent threshold records can coexist. A 15-SO perfect game may store:

```text
GAME_STRIKEOUTS_15
GAME_PERFECT_GAME
```

### Nested team pitching hierarchy

For the same team/game:

```text
TEAM_PERFECT_GAME > TEAM_NO_HIT_NO_RUN > TEAM_SHUTOUT_WIN
```

Persist only the highest team pitching achievement.

## Source semantics that must remain correct

Do not regress the Task 006 findings.

Upper batting table:

- `AB, R, H, RBI, BB, SO, LOB`: confirmed game values
- `AVG`: derived rate
- upper `HR`, `SB`: season totals; NEVER use as game deltas

Lower batting summary is authoritative for game-event counts/details:

- `Doubles:`
- `Triples:`
- `Home Runs:`
- `Stolen Bases:`

The evaluator must use lower-summary HR/SB occurrence counts, not the upper season-total columns.

Grand-slam/cycle logic must retain deterministic event evidence.

## Phase 1 — Code coverage audit

Before adding rules, produce a small coverage matrix in the final report (and optionally a dev/test helper) with one row for every requested rule/family:

```text
Requirement | Rule key/family | Evaluator implemented? | Persistence? | Unit test? | Real sample match?
```

Explicitly inspect:

- `game_rules.py`
- `game_evaluator.py`
- `game_import_service.py`
- schema/persistence code
- `tests/test_game_engine.py`

Do not infer coverage from rule names alone. Trace each rule through evaluation -> persistence -> repository/UI query.

## Phase 2 — Extend the evaluator/catalog

Implement missing threshold ladders using reusable family logic rather than one function per numeric threshold when practical.

Recommended conceptual helper:

```python
highest_reached(value, thresholds) -> threshold | None
```

Persist `threshold_value` and `achieved_value` separately.

Named predicates remain explicit special rules.

## Phase 3 — Team game evaluation

Add team-level evaluation using normalized game lines.

### Starter vs all-appearing predicates

The local worker must verify that the game-box source can distinguish starters from substitutes/other appearing batters.

If starter identity can be determined reliably:

- `TEAM_STARTERS_ALL_HIT`: every starting batter H >= 1
- `TEAM_STARTERS_ALL_RBI`: every starting batter RBI >= 1

All-appearing variants:

- `TEAM_APPEARED_ALL_HIT`: every batter who appeared H >= 1
- `TEAM_APPEARED_ALL_RBI`: every batter who appeared RBI >= 1

If starter identity cannot be proven, mark only starter-based variants unsupported and do not guess.

### Team pitching results

- Team shutout: winning team, opponent R = 0.
- Team no-hit no-run: winning team, opponent H = 0 and R = 0; may be combined pitching.
- Team perfect game: winning team and no opposing batter reaches base by any parsed route; may be combined pitching at team level.

## Phase 4 — Real-save exhaustive scan

Use the actual local `.lg` save and scan ALL available completed `game_box_*.html` / corresponding logs that are within a reasonable active/history scope available to the parser.

Goals:

1. Run the production parser/evaluator over real game files, not just three hand-picked games.
2. Report how many real matches exist for each rule/family.
3. For every rule with at least one real positive match, manually inspect at least one representative source game and verify the parsed/evaluated achievement against the actual HTML/log.
4. For rare records with no positive real sample, report `NO REAL SAMPLE`; do not treat absence as failure if the controlled fixture passes.
5. Detect parser exceptions/unknown formats across the corpus and report counts.

Do not commit raw OOTP game files.

Recommended output summary:

```text
REAL SAVE SCAN
- games scanned: N
- parse failures: N
- achievements detected: N

Hits 4+: N
Hits 5+: N
...
Grand slam: N
Cycle: N
...
```

For threshold families, report final persisted highest-only buckets rather than double-counting lower thresholds.

## Phase 5 — Controlled fixture matrix

Real saves cannot be expected to contain a 30-SO game or perfect game. Therefore create deterministic normalized fixtures or sanitized parser fixtures that exercise EVERY rule and boundary.

Required tests include at minimum:

### Hits

- 3, 4, 5, 6, 7, 8 H
- assert one achievement max, exact highest threshold

### RBI

- 4, 5, 6, 7, 8, 9, 10, 11 RBI

### HR

- 1, 2, 3, 4, 5, 6 HR
- use lower-summary/event-derived game HR value in parser-integrated test

### SB

- 2, 3, 4, 5, 6, 7, 8 SB
- use lower-summary/event-derived game SB value in parser-integrated test

### SO

- 9, 10, 14, 15, 19, 20, 24, 25, 29, 30, 31 SO

### Grand slam

- HR bases loaded -> positive
- HR bases not loaded -> negative
- ambiguous base state -> unresolved/not achieved

### Cycle

- exactly 1B+2B+3B+HR -> positive
- missing any one type -> negative
- total H sufficient but one hit type unproven -> do not guess

### Pitching hierarchy

Create separate cases for:

- complete-game win only
- shutout win with hits allowed
- no-hit no-run with at least one non-hit baserunner
- perfect game

Assert exactly one hierarchy achievement for each case.

Also test:

- complete game loss -> not `COMPLETE_GAME_WIN`
- combined team shutout -> team achievement but no individual complete-game shutout
- combined team no-hit-no-run -> team achievement but no individual no-hit-no-run

### Team batting

Fixtures must include substitutions so starter/all-appearing semantics are proven distinct.

Examples:

- all starters hit, substitute 0-for-1 -> starters-all-hit YES; appeared-all-hit NO
- every appearing batter hits -> both YES
- same pattern for RBI

### Team pitching hierarchy

- team shutout only
- team no-hit-no-run but not perfect
- team perfect game

Assert highest-only team hierarchy persistence.

## Phase 6 — Persistence and idempotency

For every family/hierarchy verify:

1. process game once -> expected rows
2. process same game again -> no duplicate rows
3. if rule evaluation for one game returns multiple independent families, all independent achievements persist
4. suppressed lower thresholds/hierarchy entries never appear in DB

Add/adjust DB uniqueness so this is structurally protected where practical.

## Phase 7 — GUI/repository coverage

Verify every persisted rule can be retrieved by the repository and displayed in `Game Achievements`.

Minimum checks:

- numeric title reflects threshold reached (e.g. `경기 6안타`, not generic `5+ hits`)
- `achieved_value` may exceed threshold and is preserved
- team achievements can render without pretending to have a player ID
- special achievements display correct context where available
- no suppressed lower achievement appears in the UI

Do not redesign the page.

## Terminology corrections

Use the project meaning:

- `완투승` = complete-game win, not merely complete game.
- `완봉승` = complete-game win with 0 opponent runs.
- `노히트 노런` = complete-game win with 0 opponent hits AND 0 opponent runs.
- `퍼펙트 게임` = no opposing batter reaches base.

If current `GAME_NO_HITTER` semantics allow runs, rename/refactor it to the stricter project rule instead of silently keeping mismatched semantics.

## Validation commands

Local only; no Actions/PR/push.

```powershell
.\.venv\Scripts\python.exe -m compileall -q src scripts
.\.venv\Scripts\python.exe -m pytest -q
```

If useful, add a local-only/read-only verification script for exhaustive save scanning. It must not copy or modify game files.

## Required report

```text
RESULT: PASS | FAIL

COVERAGE
- batter threshold families: PASS/FAIL
- batter special rules: PASS/FAIL
- pitcher thresholds: PASS/FAIL
- pitcher special hierarchy: PASS/FAIL
- team batting rules: PASS/FAIL/UNSUPPORTED
- team pitching hierarchy: PASS/FAIL/UNSUPPORTED
- highest-only suppression: PASS/FAIL

REAL SAVE SCAN
- games scanned: <n>
- parse failures: <n>
- achievements detected: <n>
- rules with real positive samples: <list>
- rules without real positive samples: <list>

FIXTURE MATRIX
- hits boundaries: PASS/FAIL
- RBI boundaries: PASS/FAIL
- HR boundaries: PASS/FAIL
- SB boundaries: PASS/FAIL
- SO boundaries: PASS/FAIL
- grand slam positive/negative: PASS/FAIL
- cycle positive/negative: PASS/FAIL
- pitcher hierarchy: PASS/FAIL
- team batting substitutions: PASS/FAIL/UNSUPPORTED
- team pitching hierarchy: PASS/FAIL/UNSUPPORTED

PERSISTENCE
- highest-only rows: PASS/FAIL
- independent achievements coexist: PASS/FAIL
- repeated-game idempotency: PASS/FAIL

GUI
- all persisted rule families visible: PASS/FAIL
- team achievements visible: PASS/FAIL

CODE/TEST CHANGES
- <summary>

REAL-SAMPLE FINDINGS
- <representative manually verified positives and source evidence>

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE or exact blockers
```

Prefer one final local feature/verification commit after all checks pass:

```text
feat: complete game milestone coverage
```

Do not push from the local worker.
