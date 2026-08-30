# Task 009 — Game Milestone Settings + Team Appeared Semantics

## Goal

Finish the game-milestone feature by:

1. simplifying `TEAM_APPEARED_*` to use the batting-table player rows exactly as OOTP presents them;
2. replacing hard-coded numeric game-milestone thresholds with persisted user-configurable values;
3. adding one compact PySide6 options dialog that edits those values;
4. rebuilding existing game achievements from the stored Game Ledger after settings change, without reparsing raw OOTP files.

Do not start season/career milestones in this task.

## Required local context

Read first:

- `docs/GAME_MILESTONE_CATALOG.md`
- `docs/MILESTONE_RULES_DESIGN.md`
- `src/ootp_milestone_tracker/milestones/game_rules.py`
- `src/ootp_milestone_tracker/milestones/game_evaluator.py`
- `src/ootp_milestone_tracker/importer/game_import_service.py`
- `src/ootp_milestone_tracker/db/schema.py`
- `src/ootp_milestone_tracker/db/repository.py`
- `src/ootp_milestone_tracker/ui/pages/milestones.py`
- `.agents/rules/workflow.md`

Current validated game parsing/semantic audit is considered baseline. Preserve all existing milestone behavior unless explicitly changed below.

## A. TEAM_APPEARED semantics — authoritative rule

The user explicitly wants `출장 전원 안타/타점` to be judged from the upper batting table itself.

Canonical participant set:

```text
all parsed player rows in the team's upper batting table
```

Do NOT reconstruct plate appearances and do NOT exclude a player row because AB/BB/etc. are zero.

The parser already converts the upper batting table into `record.batting_lines`; therefore, for a team:

```python
appeared = all batting_lines for that team
```

Exclude only non-player/header/total rows at parsing time. If OOTP emits a real player as a batting-table row, that player is part of `TEAM_APPEARED_*`.

Rules:

```text
TEAM_APPEARED_ALL_HIT
= every parsed batting-table player row has game H >= 1

TEAM_APPEARED_ALL_RBI
= every parsed batting-table player row has game RBI >= 1
```

Starter variants remain:

```text
TEAM_STARTERS_ALL_HIT
TEAM_STARTERS_ALL_RBI
```

using `is_starter=True` only.

Required tests:

- every player row H>=1 -> appeared all-hit PASS
- one player row H=0 -> FAIL
- every player row RBI>=1 -> appeared all-RBI PASS
- one player row RBI=0 -> FAIL
- substitute/non-starter row must participate in appeared rule if it exists as a batting-table player row
- same substitute must not affect starters-only rule

## B. Configurable numeric game milestone families

The following threshold families must no longer depend on immutable class constants as the production source of truth:

```text
GAME_HITS         default: 4,5,6,7
GAME_RBI          default: 5,6,7,8,9,10
GAME_HR           default: 2,3,4,5
GAME_SB           default: 3,4,5,6,7
GAME_STRIKEOUTS   default: 10,15,20,25,30
```

The default catalog remains exactly the current behavior.

User configuration must support an arbitrary ordered list of positive integer thresholds, not only start/step/end. This keeps future irregular ladders possible.

Validation rules:

- positive integers only
- remove/reject duplicates
- sort ascending before persistence
- enabled family must contain at least one threshold
- reject malformed input without partially saving

Highest-only semantics remain unchanged:

```text
configured hits = 3,5,8
H=2 -> none
H=3 -> GAME_HITS_3
H=4 -> GAME_HITS_3
H=6 -> GAME_HITS_5 only
H=9 -> GAME_HITS_8 only, achieved_value=9
```

Rule keys/titles are generated from the configured threshold:

```text
GAME_HITS_3 -> 경기 3안타
GAME_STRIKEOUTS_12 -> 경기 12탈삼진
```

Do not special-case only the original defaults.

## C. Persistence

Add a small DB-backed configuration model. Prefer a generic table rather than storing Python-specific state.

Recommended schema:

```text
game_milestone_rule_settings
- family_key TEXT PRIMARY KEY
- enabled INTEGER NOT NULL DEFAULT 1
- thresholds_json TEXT NOT NULL
```

Seed/read defaults lazily so existing DBs continue to work without destructive reset.

Recommended rows:

```text
GAME_HITS       [4,5,6,7]
GAME_RBI        [5,6,7,8,9,10]
GAME_HR         [2,3,4,5]
GAME_SB         [3,4,5,6,7]
GAME_STRIKEOUTS [10,15,20,25,30]
```

A clean fallback to defaults is required if an older DB has no settings rows yet.

Do not put the editable thresholds only in `app_settings` if a dedicated rule-settings table is cleaner in the existing architecture.

## D. Evaluator integration

The production evaluator must receive/use the persisted threshold configuration.

Do not make UI code mutate class globals.

Acceptable shape:

```python
config = repo.game_milestone_rule_settings()
achievements = evaluate_game(record, config=config)
```

or an equivalent service-owned configuration object.

Unit tests may still instantiate defaults directly.

Special named rules remain unchanged and always enabled in this task unless the existing architecture makes a generic enabled flag trivial. The mandatory user-editable part is the five numeric families above.

## E. Options popup

Add one compact modal dialog reachable from the existing Milestones page, preferably inside/near the `Game Achievements` tab.

Suggested entry point:

```text
[Game Milestone Settings]
```

Use a small `QDialog`; do not add another top-level menu.

Recommended dialog content:

```text
Game Milestone Settings

[✓] Hits          [4, 5, 6, 7]
[✓] RBI           [5, 6, 7, 8, 9, 10]
[✓] Home Runs     [2, 3, 4, 5]
[✓] Stolen Bases  [3, 4, 5, 6, 7]
[✓] Strikeouts    [10, 15, 20, 25, 30]

                  [Reset Defaults] [Cancel] [Save]
```

A comma-separated validated integer editor is acceptable and compact. A chip/spinbox implementation is also acceptable if simpler and cleaner.

Requirements:

- show current persisted values when opened
- enable/disable each numeric family
- validation message for invalid/empty enabled lists
- `Reset Defaults` updates the dialog fields; persistence occurs only on Save
- Cancel leaves DB unchanged
- Save is transactional
- use the existing compact visual language; no oversized card UI

## F. Rebuild existing game achievements after Save

This is mandatory.

Changing thresholds must affect already-imported games immediately. Do NOT require the user to delete the DB or reparse all raw `game_box_*.html` files.

After valid settings Save:

```text
persist settings
-> rebuild game_milestone_achievements from stored Game Ledger
-> refresh Game Achievements table
```

The rebuild should use existing DB ledger tables:

- `games`
- `player_game_batting`
- `player_game_pitching`
- `game_batting_events`
- any already-persisted context required by the evaluator

If some special context cannot be reconstructed from current ledger storage, do not regress existing special achievements while rebuilding numeric settings. In that case either:

1. preserve named-rule rows and rebuild only configurable numeric-family rows, or
2. first add the minimal stored evidence needed for a complete ledger-only rebuild.

Prefer the safer minimal approach: numeric settings changes should rebuild only numeric-family achievements unless full special-rule reconstruction is already guaranteed.

Rebuild requirements:

- no duplicate achievement rows
- highest-only still enforced
- disabled family rows removed from historical achievements
- re-enabled family can be rebuilt from ledger
- independent named achievements remain intact
- transaction/rollback on failure

## G. Required tests

Keep all existing tests passing and add focused coverage.

### Team appeared semantics

- all parsed rows hit -> PASS
- one parsed row zero hit -> FAIL
- all parsed rows RBI -> PASS
- one parsed row zero RBI -> FAIL
- non-starter player row included in appeared rule
- same row excluded from starters-only rule

### Threshold configuration

For each family verify defaults.

Custom example:

```text
Hits = [3,5,8]
```

Boundary matrix:

```text
2 -> none
3 -> 3
4 -> 3
5 -> 5
7 -> 5
8 -> 8
9 -> 8
```

Also test:

- unsorted input normalized
- duplicate input normalized/rejected consistently
- invalid text rejected
- zero/negative rejected
- disabled family produces no achievement
- defaults restore correctly

### Persistence/rebuild

1. import/store controlled games under defaults
2. change threshold settings
3. rebuild
4. assert historical numeric achievement rows change to new highest-only rule keys
5. special named achievement rows remain intact
6. re-run rebuild -> identical rows, no duplicates
7. reopen repository/dialog -> persisted settings still present

### GUI

- dialog opens from Milestones/Game Achievements
- current values loaded
- Save updates values
- Cancel does not
- Reset Defaults works
- invalid input cannot save
- achievement table refreshes after successful Save/rebuild

## H. Real-save regression

After implementation run the existing real-save full scan/regression path again.

Required:

- 7,682-game sample corpus (or current available count) parses with 0 failures
- default settings reproduce previous milestone counts/rules except for the deliberate `TEAM_APPEARED_*` semantic change
- spot-check at least one real `TEAM_APPEARED_ALL_HIT` / `ALL_RBI` candidate if available
- idempotency PASS

Document any count difference caused specifically by the new table-row participant semantics.

## Scope limits

Do NOT implement:

- season milestone accumulation
- career milestone accumulation
- long-term forecasts
- full general milestone preset editor
- raw OOTP file writes

This task closes the game-milestone phase and establishes the configuration pattern that season/career milestone settings can later reuse.

## Git / cost rules

- local validation only
- no GitHub Actions
- no PR
- prefer one final local commit
- do not push from local worker unless explicitly instructed by the user/top-level orchestrator

Suggested commit:

```text
feat: add configurable game milestone settings
```

## Report format

```text
RESULT: PASS | FAIL

TEAM APPEARED SEMANTICS
- batting-table rows used directly: PASS/FAIL
- all-hit boundaries: PASS/FAIL
- all-RBI boundaries: PASS/FAIL
- starter separation: PASS/FAIL

SETTINGS
- DB persistence: PASS/FAIL
- defaults: PASS/FAIL
- custom thresholds: PASS/FAIL
- enabled/disabled: PASS/FAIL
- reset defaults: PASS/FAIL
- validation: PASS/FAIL

REBUILD
- historical numeric rebuild: PASS/FAIL
- highest-only after rebuild: PASS/FAIL
- named achievements preserved: PASS/FAIL
- repeated rebuild idempotency: PASS/FAIL

GUI
- popup open/load: PASS/FAIL
- save/cancel/reset: PASS/FAIL
- automatic table refresh: PASS/FAIL

REGRESSION
- compile: PASS/FAIL
- tests: PASS/FAIL
- full-save scan: PASS/FAIL
- parse failures: <n>
- idempotency: PASS/FAIL

FIXES
- NONE or list

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE or exact blockers
```
