# Task 010 — Season Tracking, Reconciliation, and Season Milestones

## Goal

Implement production regular-season aggregation and milestone tracking on top of the validated Game Ledger, including a user-driven **Finalize Regular Season** workflow.

This task must implement the design in:

```text
docs/SEASON_TRACKING_DESIGN.md
```

Read first:

```text
.agents/rules/workflow.md
docs/SEASON_TRACKING_DESIGN.md
docs/OOTP_DATA_IMPORT_PLAN.md
docs/research/OOTP27_SOURCE_INVENTORY_LOCAL.md
docs/research/OOTP27_GAME_RECORD_RESEARCH_LOCAL.md
docs/GAME_MILESTONE_CATALOG.md
```

Do not implement career milestone ladders yet. Do build the checkpoint data required for the later career system.

No `*_rosters.txt` dependency.

---

# Phase 0 — Mandatory source verification before implementation

Before adding final-rate logic, inspect the actual local `SuperYukies_V1.0.lg` export files and document exact `player_*_stats.txt` field mappings.

Create/update:

```text
docs/research/OOTP27_SEASON_STATS_RESEARCH_LOCAL.md
```

Required evidence:

## Player stats export

For every available `player_*_stats.txt` family identify:

- exact filename;
- encoding/delimiter/header behavior;
- stable player ID field;
- season/year field;
- competition/league field if present;
- team field if present;
- whether the file contains one row per season, current season only, career data, or multiple scopes;
- all safely usable counting fields;
- all final rate fields exposed by OOTP.

Specifically verify whether authoritative fields exist for:

### Batting

```text
G
PA
AB
R
H
2B
3B
HR
RBI
BB
SO
SB
CS
HBP
SF
SH
AVG
OBP
SLG
OPS
WAR
```

### Pitching

```text
G
GS
W
L
SV
HOLD
IP / outs
BF
H
R
ER
HR
BB
SO
ERA
FIP
WHIP
WAR
```

Do not assume fields that are absent.

If `OPS` is absent but authoritative `OBP` and `SLG` are present, `OPS = OBP + SLG` is allowed.

If `FIP` is absent, do **not** invent a league constant. Mark final FIP milestone support unavailable unless a deterministic OOTP source/formula constant is proven.

## Postseason/progression evidence

Inspect actual available sources for deterministic evidence of:

```text
POSTSEASON_BERTH
DIVISION_CHAMPION
WILD_CARD_SERIES_WIN
DIVISION_SERIES_WIN
LEAGUE_CHAMPIONSHIP_SERIES_WIN
WORLD_SERIES_WIN
```

Search, in priority order:

1. `messages/message*.txt`
2. game-box/postseason metadata
3. other already-existing save text/HTML sources found by the source scanner

Record exact message text patterns, IDs, team links, game/series identifiers, and dates when available.

Do not guess playoff clinches from generic wording.

If a category truly does not exist in the sample, report `NOT AVAILABLE IN SAMPLE` and keep its evaluator source-safe rather than fabricating a real-data PASS.

## Broader Game Ledger fields

Reinspect batting/pitching game sources and list additional per-game fields that can safely be persisted even if no current milestone uses them.

Add proven fields to normalized models/DB as appropriate.

The principle is:

> Game Ledger = reusable local OOTP database, not a milestone-only cache.

---

# Phase 1 — Schema and season state

Add/migrate persistent season concepts. Exact table names may adapt to the current schema, but the model must support all of the following.

## `season_states`

Minimum semantics:

```text
season
tracked_team_id
competition_type
regular_season_game_target
processed_team_games
status
finalized_at nullable
checkpoint_id nullable
```

Recommended status values:

```text
active
eligible_to_finalize
finalized_reconciled
finalized_unreconciled
needs_reconcile
```

## `stats_checkpoints`

Store accepted manual OOTP export checkpoints:

```text
id
checkpoint_type
season
created/accepted time
source path(s)
source hash(es)
source modified time if available
represented game cutoff/snapshot
validation status
```

Checkpoint types:

```text
preseason
regular_season_final
manual_reconcile
```

## Season aggregates

Use or cleanly migrate the existing batting/pitching season tables so the key contains:

```text
player_id + season + competition_type
```

Support:

- live ledger-derived counting values;
- final/reconciled OOTP values;
- finalization status/source provenance;
- all fields proven in Phase 0 that are useful for DB viewing/future milestones.

Do not merge postseason into regular-season rows.

## Team season stats

At minimum preserve:

```text
team_id
season
competition_type
G
W
L
```

Derive from distinct processed games.

## Reconciliation records

Preserve per-field differences instead of silently overwriting history:

```text
ledger_value
export_value
adjustment
checkpoint_id
player_id
season
stat_key
```

## `season_milestone_achievements`

Minimum:

```text
entity_type
entity_id
season
competition_type
rule_key
threshold_value nullable
achieved_value
achieved_game_id nullable
achieved_date nullable
source
context/evidence nullable
```

Required unique identity must prevent duplicate rebuilds.

Sources include:

```text
game_crossing
final_export
postseason_event
```

---

# Phase 2 — Live season aggregation

Extend game import processing so every newly accepted/changed regular-season GameRecord updates/rebuilds affected season aggregates.

Important:

- same unchanged game processed twice -> no changes;
- corrected/changed game source -> rebuild affected season slice safely;
- use `outs`, not floating IP, for pitching accumulation;
- regular-season only for the season milestones below;
- postseason stays separate.

At minimum live aggregates must support all requested counting milestones:

### Batter

```text
H
HR
RBI
R
SB
```

### Pitcher

```text
outs/IP
SO
W
HOLD
SV
```

### Team

```text
G
W
L
```

Also persist other Phase-0 proven game fields where practical.

---

# Phase 3 — Season counting milestone engine

Implement configurable threshold families.

Unlike game milestones, season thresholds persist **each threshold when crossed over time**.

Example:

```text
150 H reached on June 20 -> save SEASON_HITS_150
200 H reached on Sep 10  -> save SEASON_HITS_200
```

Do not delete the 150-H achievement when 200 is later reached.

If one game crosses multiple thresholds, save every newly crossed threshold at that game.

Store exact crossing `game_id` and `game_date` from the ledger.

## Batter defaults

Hits:

```text
150, 200, 250, 300, 350
```

Home Runs:

```text
20, 30, 40, 50, 60, 70, 80, 90, 100
```

RBI:

```text
75, 100, 125, 150, 175, 200
```

Runs:

```text
75, 100, 125, 150, 175, 200
```

Stolen Bases:

```text
20, 30, 40, 50, 60, 70, 80, 90, 100
```

## Pitcher defaults

Innings:

```text
150, 200, 250, 300, 350
```

Convert thresholds to outs internally.

Strikeouts:

```text
150, 200, 250, 300, 350, 400
```

Wins:

```text
10, 15, 20, 25, 30
```

Holds:

```text
10, 15, 20, 25, 30
```

Saves:

```text
20, 30, 40, 50, 60, 70
```

## Team win defaults

```text
100, 110, 120, 130, 140
```

Use tracked team's regular-season win count.

## Rebuild semantics

Changing threshold settings must rebuild numeric season achievement rows from the existing ledger **without reparsing OOTP source files**.

Named/postseason achievements must survive numeric rebuilds.

---

# Phase 4 — Season milestone settings

Reuse the game-milestone settings architecture instead of making a separate ad-hoc settings mechanism.

Defaults must be exactly the lists in this task.

Allow users to edit/enable/disable numeric season threshold families for:

```text
H
HR
RBI
R
SB
IP
SO
W
HOLD
SV
TEAM_W
AVG
OBP
OPS
ERA bucket enablement
FIP bucket enablement
```

Also add settings:

```text
regular_season_game_target = 162
batting_rate_pa_per_team_game = 3.1
pitching_rate_ip_per_team_game = 1.0
```

Validate positive numeric lists, remove duplicates, sort deterministically, and support reset to defaults.

---

# Phase 5 — Regular-season finalization eligibility

Default MLB behavior:

```text
regular_season_game_target = 162
```

Count only processed games for the tracked team where:

```text
season = active season
competition_type = regular_season
tracked team is home or away
```

Use distinct `game_id`.

Tests must prove:

```text
161 / target 162 -> Finalize disabled
162 / target 162 -> Finalize enabled
163 / target 162 -> Finalize enabled

143 / configured 144 -> disabled
144 / configured 144 -> enabled
```

Do not count postseason/spring/international games.

---

# Phase 6 — UI: Update Games + Finalize Regular Season

Place **Finalize Regular Season** adjacent to the current game-box refresh/import action.

The current repository may not yet expose the game import action prominently. If no production refresh button exists, create one compact data control group rather than adding a new top-level navigation item.

Preferred labels:

```text
[Update Game Records] [Finalize Regular Season]
```

A suitable location is the existing Tools/data utility area unless the current local UI already has a better refresh control location.

Button states:

```text
disabled before target games
enabled at/after target games
already-finalized state does not duplicate work
```

Show compact status nearby, e.g.:

```text
Regular Season 2028 · 162 / 162 games processed · Ready to finalize
```

---

# Phase 7 — Finalize Regular Season workflow

On button click:

1. Resolve active season and tracked team.
2. Confirm eligibility again in service code; do not trust UI enabled state alone.
3. Locate current `player_*_stats.txt` files under the selected `.lg` save.
4. Validate that the files actually contain the season being finalized.
5. Validate that they are fresh enough to represent the completed season.
6. If valid, show a concise confirmation/reconciliation summary and proceed.
7. If missing/stale/invalid, show a modal that clearly says a new OOTP Player Stats export is recommended.
8. Provide actions such as:

```text
Recheck
Browse / open relevant export location if existing UI supports it
Continue Without Export
Cancel
```

Do not hard-block explicit `Continue Without Export`.

### Stale file handling

An old file remaining on disk must not be accepted merely because it exists.

At minimum reject when:

- finalizing season is absent;
- file is identical to an obsolete accepted checkpoint where a fresh one is required;
- validated counting evidence clearly shows the export materially trails the processed full-season ledger.

Use actual Phase-0 fields for deterministic validation.

Small discrepancies are not grounds for rejection; they should become reconciliation differences.

---

# Phase 8 — Reconciliation

When a valid final export is available:

```text
ledger aggregate
   vs
OOTP exported season row
   -> reconciliation record
   -> OOTP value becomes authoritative final season value
```

Preserve differences by field.

Do not alter or duplicate game milestone achievements.

### Counting milestone correction rules

After final reconciliation:

1. If OOTP final total confirms an existing game-crossing milestone, keep it with its exact game.
2. If OOTP authoritative final total is below a threshold that the ledger falsely recorded, remove/invalidate that season milestone.
3. If OOTP authoritative final total reaches a threshold that the ledger missed, create a season milestone with:

```text
source = final_export
achieved_game_id = NULL
```

Do not fabricate an exact achievement game.

---

# Phase 9 — Final rate milestones

Evaluate these only when the regular season is finalized/reconciled, or when an unreconciled ledger can prove the value from complete components.

Prefer authoritative OOTP export rates.

Apply configured qualification before awarding rate milestones.

Default MLB-oriented qualifiers:

```text
batting: 3.1 PA per configured team game
pitching: 1.0 IP per configured team game
```

Use the actual configured regular-season target.

## Batter rate defaults

AVG:

```text
.275, .300, .325, .350, .375, .400
```

OBP:

```text
.350, .375, .400, .425, .450, .475, .500
```

OPS:

```text
.800, .900, 1.000, 1.100, 1.200, 1.300, 1.400, 1.500
```

For each final rate family store the highest qualifying tier for that finalized season.

Examples:

```text
AVG .361 -> SEASON_AVG_350 only
OPS 1.137 -> SEASON_OPS_1100 only
```

Preserve actual achieved rate separately.

## Pitcher final buckets

ERA:

```text
2.xx
1.xx
0.xx
```

FIP:

```text
2.xx
1.xx
0.xx
```

Store only the actual final bucket.

Do not represent 1.75 ERA as both 2-point and 1-point milestones.

If FIP is not proven from OOTP export/source, report it as unsupported rather than approximating it.

---

# Phase 10 — Continue without export / late reconcile

If the user explicitly continues without a valid export:

```text
season status = finalized_unreconciled
```

Requirements:

- keep ledger counting totals;
- keep confirmed counting milestones;
- calculate only rate stats whose required components are complete and proven;
- skip unsupported final rates rather than guess;
- allow `Reconcile Finalized Season` later when a fresh export exists.

Late reconciliation must be idempotent and update only affected season/final-rate records.

If a corrected regular-season game is imported after finalization, mark the season `needs_reconcile` rather than silently pretending the final snapshot is unchanged.

---

# Phase 11 — Postseason/team progression achievements

Implement the following as named team season/event achievements when deterministic source evidence is proven:

```text
POSTSEASON_BERTH        = 포스트시즌 진출
DIVISION_CHAMPION       = 디비전 우승 확정
WILD_CARD_SERIES_WIN    = 와일드 카드 시리즈 우승
DIVISION_SERIES_WIN     = 디비전 시리즈 우승
LEAGUE_CHAMPIONSHIP_SERIES_WIN = 리그 챔피언십 시리즈 우승
WORLD_SERIES_WIN        = 월드 시리즈 우승
```

These are not regular-season counting totals and may occur before/after regular-season finalization.

Store event date and evidence/context text when available.

Do not use vague win-count heuristics unless the exact playoff format/series identity has been proven.

If the current save lacks a specific series category, controlled fixtures can verify evaluator behavior, but the report must say `NOT AVAILABLE IN SAMPLE` for real positive sample status.

---

# Phase 12 — Season UI

Keep the top-level menu architecture unchanged.

Extend existing pages rather than adding a top-level `Season` menu.

Minimum usable UI:

## Players / records view

Allow season rows to display finalized/live values with visible state:

```text
LIVE
FINAL
UNRECONCILED
```

## Milestones page

Add/extend season achievement filtering so users can see:

```text
Date | Player/Team | Season | Competition | Milestone | Value | Source/Context
```

Counting achievements should show the achievement game/date when known.

Final rate achievements may show `Season Final` rather than a fabricated game date.

## Finalization summary

After finalization show a compact result:

```text
2028 Regular Season finalized
Players reconciled: N
Adjusted fields: N
Counting milestones added/removed: N/N
Final rate milestones: N
Status: reconciled | unreconciled
```

---

# Phase 13 — Preseason recommendation

Because future career tracking depends on a clean checkpoint, add a non-blocking recommendation when a new regular season is detected and no preseason/current trusted checkpoint exists.

Suggested message:

```text
A new season was detected.
Exporting OOTP player stats before the season is recommended to establish a clean career baseline.
```

Do not require the export to play/import games.

Accept/import a valid preseason checkpoint when supplied and preserve career totals for future Task(s).

---

# Tests — mandatory

Local only. No GitHub Actions / PR / remote push.

## Source/parser tests

- actual player stats files parse successfully;
- current season detection from export works;
- stale previous-season file rejected;
- stale earlier-current-season file detection proven where fixture/sample permits;
- fresh full-season export accepted;
- all added ledger fields match actual source samples.

## Aggregation tests

- regular vs postseason separation;
- player batting sums;
- pitcher outs/IP sums;
- W/HOLD/SV sums;
- team G/W/L;
- changed-game rebuild/idempotency.

## Counting boundary matrix

Test every threshold family with below/exact/above values and sequential crossings.

Examples:

```text
H 149 -> none
H 150 -> 150
later H 200 -> existing 150 preserved + new 200
```

Test one-game multiple-threshold crossing using controlled fixtures even if unrealistic.

## Finalize activation

- 161/162 disabled;
- 162/162 enabled;
- custom target boundaries;
- postseason games do not activate it.

## Reconciliation

- exact parity;
- small adjustment;
- false ledger milestone removed when final authoritative value is below threshold;
- missed threshold added with `source=final_export` and no fake game ID;
- repeated finalization/reconciliation creates no duplicates.

## Rate milestones

Controlled matrix for all thresholds and qualifiers:

- just below/exact/above each AVG/OBP/OPS threshold;
- unqualified high rate -> no milestone;
- qualified high rate -> highest final tier only;
- ERA 2.99 -> 2.xx;
- ERA 1.99 -> 1.xx;
- ERA 0.99 -> 0.xx;
- ERA 3.00 -> none;
- equivalent FIP cases when supported.

## Continue without export

- explicit continue succeeds;
- season becomes `finalized_unreconciled`;
- no guessed unsupported rate milestone;
- later fresh export reconciliation succeeds.

## Team postseason events

- positive/negative controlled fixtures for every implemented source pattern;
- real sample parity for every category available in sample.

## Regression

```powershell
.\.venv\Scripts\python.exe -m compileall -q src scripts
.\.venv\Scripts\python.exe -m pytest -q
```

Run the existing full-save game scan and require parse failures = 0.

GUI smoke:

- update games control;
- finalization enable/disable;
- stale export modal;
- continue without export;
- reconciled completion summary;
- season milestone view;
- settings persistence/reset.

---

# Required report

```text
RESULT: PASS | FAIL

PLAYER STATS SOURCE
- batting export mapping: PASS/FAIL
- pitching export mapping: PASS/FAIL
- final AVG/OBP/OPS: PASS/FAIL/UNAVAILABLE
- final ERA/FIP: PASS/FAIL/UNAVAILABLE
- stale-export detection: PASS/FAIL

LEDGER / SEASON AGGREGATION
- broader game fields: PASS/FAIL
- batting aggregate: PASS/FAIL
- pitching aggregate: PASS/FAIL
- team aggregate: PASS/FAIL
- competition separation: PASS/FAIL
- rebuild/idempotency: PASS/FAIL

SEASON COUNTING MILESTONES
- batter H/HR/RBI/R/SB: PASS/FAIL
- pitcher IP/SO/W/HOLD/SV: PASS/FAIL
- team W: PASS/FAIL
- sequential threshold preservation: PASS/FAIL

FINALIZATION
- 162 default gate: PASS/FAIL
- configurable target: PASS/FAIL
- fresh export accepted: PASS/FAIL
- stale export rejected: PASS/FAIL
- continue without export: PASS/FAIL
- late reconcile: PASS/FAIL

RATE MILESTONES
- AVG: PASS/FAIL/UNAVAILABLE
- OBP: PASS/FAIL/UNAVAILABLE
- OPS: PASS/FAIL/UNAVAILABLE
- ERA: PASS/FAIL/UNAVAILABLE
- FIP: PASS/FAIL/UNAVAILABLE
- qualification: PASS/FAIL

TEAM PROGRESSION
- postseason berth: CONFIRMED/NOT AVAILABLE/FAIL
- division champion: CONFIRMED/NOT AVAILABLE/FAIL
- wild card series: CONFIRMED/NOT AVAILABLE/FAIL
- division series: CONFIRMED/NOT AVAILABLE/FAIL
- LCS: CONFIRMED/NOT AVAILABLE/FAIL
- world series: CONFIRMED/NOT AVAILABLE/FAIL

GUI
- update games + finalize controls: PASS/FAIL
- finalization modal/summary: PASS/FAIL
- season milestone view: PASS/FAIL
- season settings: PASS/FAIL

REGRESSION
- compile: PASS/FAIL
- tests: PASS/FAIL
- full-save scan: PASS/FAIL
- parse failures: <n>

FILES
- docs/research/OOTP27_SEASON_STATS_RESEARCH_LOCAL.md

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE
or
- <exact blocker>
```

Suggested local commit:

```text
feat: add season aggregation and finalization workflow
```

Do not push. Return the report to the top-level assistant for review before starting career milestones.
