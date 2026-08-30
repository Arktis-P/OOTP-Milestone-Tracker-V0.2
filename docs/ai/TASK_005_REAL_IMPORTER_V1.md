# Task 005 — Real OOTP Importer v1 (Player Stats Only)

## Goal

Replace the sample-only data path with the first real-data import path using only:

```text
import_export/player_*_stats.txt
```

Do **not** require or parse `*_rosters.txt` for routine import. The user can export player stats with one action, while roster export requires repeated league selection.

This task ends when the current Player Records UI can display real OOTP players/stat rows from the selected `.lg`, with competition types separated and import history stored.

## Read first

- `docs/research/OOTP27_SOURCE_INVENTORY_LOCAL.md`
- `docs/OOTP_DATA_IMPORT_PLAN.md`
- `docs/MILESTONE_RULES_DESIGN.md`
- `docs/MILESTONE_ACHIEVEMENT_MODEL.md`
- current DB schema/repository/importer modules

Do not re-investigate unrelated repository areas.

## Confirmed local facts

- `player_id` is Field 0 / stable primary player key.
- player-stat files are UTF-8 with BOM CSV.
- `team_id` and `year` exist as secondary identities where applicable.
- career additive counting totals can be derived by grouping normalized season records.

Inspect exact real headers/rows for mappings not already documented. Do not guess column indexes.

## Mandatory competition split

The importer must keep these separate from the first real DB import:

```text
regular_season
postseason
spring_training
international
```

Determine exactly how the local `player_*_stats.txt` exports distinguish these categories (filename, directory, field, or export family). Record the mapping in code constants/metadata and in the final report.

If one category cannot be mapped safely from the available export, report that category as a blocker/unsupported source. Do not merge it into regular season.

## Architecture

Recommended:

```text
importer/
├─ source_locator.py
├─ source_scanner.py
├─ models.py
├─ player_stats_parser.py
├─ normalizer.py
└─ import_service.py
```

No roster parser is required.

UI/Repository code must not parse OOTP files directly.

## Player/team identity without roster files

Use only fields available in `player_*_stats.txt` for routine import.

Attempt to normalize, when actually present:

- `player_id`
- English player name
- `team_id`
- team name/abbreviation
- position
- active/current status if available
- season/year

If a display field is absent, keep it nullable/default and document the limitation. Never silently read roster files to fill gaps.

The current UI may need a safe placeholder for missing team/position metadata; keep that minimal.

## Stats mapping

Map real fields required by the current GUI when present.

Batting target fields:

```text
G PA AB H HR RBI BB SO SB AVG OBP SLG WAR
```

Pitching target fields:

```text
G GS W L SV IP SO ERA WHIP WAR
```

Do not fabricate unavailable rate/advanced fields.

## DB change required

The old primary key `(player_id, season)` is insufficient.

Season stat identity must become at least:

```text
(player_id, season, competition_type)
```

Apply the equivalent change to batting and pitching season tables.

Current/career queries must accept or explicitly choose a `competition_type`; default UI behavior may initially show `regular_season`, but data for other contexts must remain separate.

## Import history

Add/maintain:

```text
import_runs
stat_snapshots
```

Snapshot identity/value data must include:

```text
entity_type
entity_id
scope
competition_type
season nullable
stat_key
value
```

Snapshot only useful milestone/current-UI stats, not every raw field.

Repeated unchanged import:

- no duplicate current rows,
- no duplicate snapshot set,
- no duplicate achievement.

## Career totals

For additive counting stats, derive career totals by summing normalized season rows **inside the same competition type**.

Examples:

```text
regular-season career H != postseason career H
regular-season career W != international career W
```

Do not combine contexts.

## Milestone crossing preparation

Task 005 does not need to resolve exact game situations yet, but data must support:

```text
previous < threshold <= current
```

When a rule crosses, the later achievement engine will record an unresolved achievement and Task 006 will enrich it from game sources.

Do not use messages/box scores/logs in Task 005 unless strictly necessary to identify the player-stat competition type; if so, stop and report rather than expanding scope automatically.

## Forecast scope

Do not implement multi-year forecasts.

If a minimal forecast is added, it may only return:

```text
likely_this_season
unlikely_this_season
already_achieved
unknown
```

Only calculate when remaining schedule information is reliable. Otherwise `unknown`.

Forecasting is lower priority than correct import and may be deferred.

## GUI integration

Keep UI redesign out of scope.

Add/use one compact `Import / Refresh data` action:

1. selected/auto-detected `.lg` path,
2. import player stats,
3. refresh repository-backed pages,
4. concise result/error summary.

The sample reset path remains available for development.

## Required local validation

Run locally only:

1. sync latest `origin/user/Workspace`, preserving local research commit/work.
2. compileall.
3. existing pytest.
4. parser tests with sanitized tiny rows where useful.
5. import actual local save.
6. verify stable `player_id` values.
7. verify competition-type mapping from real files.
8. verify one batter source parity.
9. verify one pitcher source parity.
10. verify one multi-season player and career sum.
11. verify regular/post/spring/international never collide in DB keys.
12. import unchanged source again and verify idempotency.
13. GUI real-data smoke.

Do not claim PASS from counts alone.

## Explicit forbidden actions

- Do not require `*_rosters.txt`.
- Do not merge competition types.
- Do not parse all messages/box/log files yet.
- Do not push from local worker.
- Do not open PR or run GitHub Actions.
- Do not redesign the GUI.

## Suggested local commit

```text
feat: import real OOTP player stats by competition
```

## Report format

```text
RESULT: PASS | FAIL

IMPORT
- save: <name>
- player stat files: <n>
- players: <n>
- batting seasons: <n>
- pitching seasons: <n>
- snapshots: <n>

COMPETITION MAPPING
- regular_season: <source mapping / PASS/FAIL>
- postseason: <source mapping / PASS/FAIL>
- spring_training: <source mapping / PASS/FAIL>
- international: <source mapping / PASS/FAIL>

CHECKS
- compile: PASS/FAIL
- existing tests: PASS/FAIL
- player stats parser: PASS/FAIL
- stable player IDs: PASS/FAIL
- DB upsert: PASS/FAIL
- competition separation: PASS/FAIL
- repeated import idempotency: PASS/FAIL
- GUI real-data smoke: PASS/FAIL
- batter source parity: PASS/FAIL
- pitcher source parity: PASS/FAIL
- career aggregation: PASS/FAIL
- snapshot history: PASS/FAIL

FIELD MAPPING NOTES
- <only material mappings/limitations>

FIXES
- NONE or <changes>

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE or <exact blocker>
```
