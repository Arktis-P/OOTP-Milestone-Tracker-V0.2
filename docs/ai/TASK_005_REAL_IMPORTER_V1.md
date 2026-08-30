# Task 005 — Real OOTP Importer v1

## Goal

Replace the sample-only data path with a first real-data import path using the locally confirmed OOTP 27 save sources.

This task is intentionally limited to the two source families required to populate the current Player Records UI:

1. `import_export/*_rosters.txt`
2. `import_export/player_*_stats.txt`

Do not parse messages, game boxes, or logs yet. Those sources belong to later event/game milestone work.

## Required local context

Before coding, read:

- `docs/research/OOTP27_SOURCE_INVENTORY_LOCAL.md`
- `docs/OOTP_DATA_IMPORT_PLAN.md`
- `docs/MILESTONE_RULES_DESIGN.md`
- `src/ootp_milestone_tracker/db/schema.py`
- `src/ootp_milestone_tracker/importer/source_locator.py`
- `src/ootp_milestone_tracker/importer/source_scanner.py`

Use the actual local `.lg` save only as a read-only source. Never modify or commit the save files.

The local research already confirmed:

- common player primary key: `player_id`
- roster player id: field 0
- player stats player id: field 0
- secondary keys: `team_id`, `game_id`, `year`
- roster/stats encoding: UTF-8 with BOM CSV
- career totals can be derived by grouping season stats by `player_id`

Do not guess column indexes that are not explicitly documented in the local research report. Inspect the real header/rows when necessary and record the mapping in code constants or parser metadata.

## Required architecture

Keep source parsing separate from SQLite writing.

Recommended package layout:

```text
src/ootp_milestone_tracker/importer/
├─ source_locator.py
├─ source_scanner.py
├─ models.py
├─ roster_parser.py
├─ player_stats_parser.py
├─ normalizer.py
└─ import_service.py
```

### 1. Parsed/normalized models

Create small dataclasses or typed records for normalized data. At minimum:

- Team
- Player
- BattingSeason
- PitchingSeason

The UI and Repository must never parse OOTP text files directly.

### 2. Roster parser

Parse the confirmed roster CSV files and produce normalized team/player identity data.

Required identity fields where available from the actual source:

- `player_id`
- `team_id`
- English player name
- position
- active/roster state
- age or birth date source sufficient to derive display age
- team name / abbreviation if present

If team names are not fully available from roster files, use the documented local source relationship rather than inventing values.

### 3. Player stats parser

Parse the confirmed `player_*_stats.txt` files.

At minimum, map the fields required by the current GUI schema when present:

Batting:
- season/year
- G, PA, AB, H, HR, RBI, BB, SO, SB
- AVG, OBP, SLG, WAR if supplied

Pitching:
- season/year
- G, GS, W, L, SV, IP, SO
- ERA, WHIP, WAR if supplied

If a current GUI field is not supplied by OOTP in the inspected file, keep a documented default instead of fabricating a value.

### 4. Normalizer

The normalizer owns OOTP-specific conversion details:

- UTF-8 BOM handling
- numeric conversion
- blank/null handling
- position normalization
- season integer conversion
- innings-pitched representation if needed
- duplicate rows

Parsers should produce source-shaped data; the normalizer produces app-shaped data.

## Database behavior

Do not destroy the sample seed path. Real import and sample reset must remain separately usable during development.

### Current-state tables

Use/update the current tables for the latest imported state:

- `teams`
- `players`
- `batting_seasons`
- `pitching_seasons`

OOTP `player_id` and `team_id` should remain the stable source identities where safely possible.

Use idempotent UPSERT behavior so importing the same save twice does not duplicate rows.

### Import history

Add the minimum history required for later milestone detection and forecasting.

Recommended tables:

```text
import_runs
- id
- imported_at
- save_path
- save_name
- source_modified_at or source signature
- status

stat_snapshots
- import_run_id
- entity_type
- entity_id
- scope
- season nullable
- stat_key
- value
```

For v1, snapshot only the stats already needed by configured milestone rules and the current Player Records UI. Do not create a giant generic copy of every OOTP field.

The current-state season tables are for fast UI queries. `stat_snapshots` are append-only history for milestone crossing detection and later forecasts.

Do not snapshot duplicate data if the selected save has not materially changed; use a simple source signature/modified-time strategy documented in code.

## Import service

Expose one service-level operation, conceptually:

```python
result = import_save(save_path)
```

The service should:

1. validate `.lg` path,
2. locate roster/stat source files,
3. parse,
4. normalize,
5. start an import run,
6. upsert current state,
7. append required snapshots,
8. commit transaction,
9. return an import summary.

Import summary should include at least:

- save name
- teams imported
- players imported
- batting season rows
- pitching season rows
- snapshots written
- skipped/invalid rows
- warnings

A failed import must roll back current-state writes and mark/report failure cleanly.

## First integration surface

Do not redesign the GUI in this task.

Add the smallest useful integration point:

- Settings already stores/auto-detects the `.lg` save path.
- Add a compact `Import / Refresh data` action in Settings or the existing top-level refresh action if one already exists.
- On success, refresh repository-backed pages.
- Display a concise success/failure summary; do not build an elaborate import UI yet.

Keep the sample DB reset tool available.

## Milestone rules

Do not implement the full milestone-rule editor in this task.

However, importer/snapshot code must not hard-code one specific hit milestone. Store generic stat keys so later rules can select:

```text
entity_type + scope + stat_key
```

Examples:

- player + career + H
- player + season + HR
- player + career + W

Career values should be derived from the normalized season rows for additive counting stats unless the local research establishes a better authoritative source.

## Validation order

Use local validation only. No GitHub Actions.

1. Sync remote without losing the existing local research commit.
2. `compileall`
3. existing pytest
4. parser tests using tiny sanitized/local fixture rows where practical
5. import the actual local test save
6. verify DB counts and stable IDs
7. run GUI
8. verify real players appear
9. verify at least one batter's season rows against OOTP source
10. verify at least one pitcher's season rows against OOTP source
11. import same unchanged save again and confirm no duplicate current-state rows
12. verify import history/snapshot behavior

## Required spot checks

Choose at least:

- one active batter from tracked team
- one active pitcher from tracked team
- one player with multiple seasons

For each, compare OOTP source values to SQLite values for representative counting and rate stats.

Do not claim PASS based only on row counts.

## Git / cost rules

- Local validation only.
- No GitHub Actions.
- No PR.
- Do not push from the local worker.
- Use checkpoint local commits only when necessary.
- Prefer one final local commit for this feature after tests pass.

Suggested commit:

```text
feat: import real OOTP roster and player stats
```

## Report format

```text
RESULT: PASS | FAIL

IMPORT
- save: <name>
- teams: <n>
- players: <n>
- batting seasons: <n>
- pitching seasons: <n>
- snapshots: <n>

CHECKS
- compile: PASS/FAIL
- existing tests: PASS/FAIL
- roster parser: PASS/FAIL
- player stats parser: PASS/FAIL
- DB upsert: PASS/FAIL
- repeated import idempotency: PASS/FAIL
- GUI real-data smoke: PASS/FAIL
- batter source parity: PASS/FAIL
- pitcher source parity: PASS/FAIL
- snapshot history: PASS/FAIL

FIELD MAPPING NOTES
- <only mappings/ambiguities that matter>

FIXES
- NONE
or
- <changes>

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE
or
- <exact blocker>
```
