# Season Tracking and Finalization Design

## Purpose

Season tracking sits on top of the already-validated per-game ledger.

The application must distinguish three kinds of truth:

```text
1. Game Ledger
   = what the app observed game by game

2. Live Season Aggregate
   = sum/derivation from processed game ledger rows

3. OOTP Stats Checkpoint
   = manually exported player_*_stats.txt, treated as authoritative reconciliation data
```

The recommended user workflow is:

```text
Before regular season
  -> export player_*_stats.txt once
  -> import as preseason baseline/checkpoint

During regular season
  -> process game_box_*.html after games
  -> update all safely extractable game-ledger stats
  -> update live regular-season aggregates
  -> immediately record counting-stat season milestones when crossed

After the configured regular-season game target is reached
  -> enable "Finalize Regular Season"
  -> validate a fresh player_*_stats.txt export for that season
  -> reconcile live aggregates against OOTP export
  -> finalize rate stats and rate milestones
  -> preserve reconciliation differences

Postseason
  -> continues separately under competition_type=postseason
  -> postseason/team-series achievements can continue after regular-season finalization
```

`*_rosters.txt` must not become a requirement.

---

## Competition boundary

The season milestones in this document use `regular_season` unless explicitly described as postseason/team progression.

Never mix:

```text
regular_season
postseason
spring_training
international
```

Player regular-season aggregate identity:

```text
(player_id, season, regular_season)
```

Team regular-season aggregate identity:

```text
(team_id, season, regular_season)
```

Postseason series achievements are event achievements for the same year/season but are not added to regular-season counting totals.

---

## Game Ledger completeness principle

The Game Ledger is a local OOTP baseball database, not merely a milestone cache.

When a per-game statistic can be extracted reliably, preserve it even when no current milestone uses it.

Existing validated examples include:

### Batting

```text
AB
R
H
RBI
BB
SO
LOB
2B
3B
HR
SB
```

### Pitching

```text
outs
H
R
ER
BB
SO
HR
BF
pitches
W
L
SV
HOLD
```

Before season aggregation is finalized, inspect the actual OOTP game-box/log sources again for additional safe per-game fields such as PA/HBP/SF/SH/CS/IBB/GIDP or other fields. Add only fields proven from the source; do not invent or infer unsafe values.

This broader ledger is required so future season/career views and milestones do not require reparsing architecture changes.

---

## Preseason checkpoint

A preseason `player_*_stats.txt` export is strongly recommended.

Its purposes are:

- establish clean career totals before the new season;
- establish a zero/current-season boundary;
- capture player IDs and historical totals available from OOTP;
- create a trusted career baseline for future career milestone work;
- prevent old game files already represented by the export from being added again.

Recommended checkpoint metadata:

```text
checkpoint_id
checkpoint_type = preseason | regular_season_final | manual_reconcile
season
created_at
accepted_at
save_path
source_files
source_hashes
source_modified_at
represented_game_cutoff / represented_game_ids
status
```

Raw OOTP exports must not be committed to Git.

---

## Live season aggregation

For each newly accepted regular-season game:

```text
GameRecord
  -> persist full player game lines
  -> rebuild/update affected season aggregates
  -> evaluate season counting milestones
  -> persist any newly crossed threshold(s) with exact game_id/game_date
```

Counting fields are summed from the game ledger.

Examples:

```text
season H  = SUM(player_game_batting.h)
season HR = SUM(player_game_batting.hr)
season R  = SUM(player_game_batting.r)
season RBI = SUM(player_game_batting.rbi)
season SB = SUM(player_game_batting.sb)

season IP outs = SUM(player_game_pitching.outs)
season SO = SUM(player_game_pitching.so)
season W = SUM(player_game_pitching.win)
season HOLD = SUM(player_game_pitching.hold)
season SV = SUM(player_game_pitching.save)
```

Team wins:

```text
count regular-season processed games where tracked team score > opponent score
```

Use distinct `game_id` and the tracked team's actual home/away identity.

---

## Season milestone crossing semantics

Season thresholds do **not** use the game-milestone highest-only suppression model across the whole season.

Each threshold is a distinct achievement when first crossed.

Example:

```text
Game A: career-in-season H goes 149 -> 151
  -> record SEASON_HITS_150 at Game A

Later Game B: 199 -> 201
  -> record SEASON_HITS_200 at Game B
```

Both remain permanently recorded.

If one game legitimately crosses more than one configured season threshold, record each crossed threshold with the same game reference.

Reprocessing/rebuilding must remain idempotent.

---

## Default player season milestones

### Batter counting milestones — immediate during season

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

### Batter final rate milestones — evaluate/finalize at regular-season finalization

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

For higher-is-better rate ladders, persist the highest qualifying final tier unless a later product decision requires every lower final tier to be shown.

Rate milestones must use finalized/reconciled season values, not a temporary midseason value.

---

## Default pitcher season milestones

### Counting milestones — immediate during season

Innings Pitched:

```text
150, 200, 250, 300, 350 IP
```

Internally compare using outs to avoid floating-point inning errors:

```text
150 IP = 450 outs
200 IP = 600 outs
...
```

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

### Final rate/bucket milestones — regular-season finalization

ERA buckets:

```text
2.xx
1.xx
0.xx
```

FIP buckets:

```text
2.xx
1.xx
0.xx
```

These are mutually exclusive final buckets. Prefer the strongest/lower bucket only.

Interpretation:

```text
2.xx -> 2.00 <= value < 3.00
1.xx -> 1.00 <= value < 2.00
0.xx -> 0.00 <= value < 1.00
```

If OOTP's export exposes authoritative ERA/FIP, prefer those finalized values. Do not guess a FIP constant.

---

## Rate qualification

A rate milestone should not be awarded to a tiny sample by default.

Default MLB-oriented qualification settings:

```text
batting_rate_pa_per_team_game = 3.1
pitching_rate_ip_per_team_game = 1.0
```

For a 162-game target this corresponds to the familiar MLB qualified-season scale.

These qualification settings must be configurable. If exact OOTP export fields or league-specific qualification rules are available and validated later, they may supersede these defaults.

Do not silently award AVG/OBP/OPS/ERA/FIP milestones to unqualified players.

---

## Team regular-season milestones

Wins — immediate when crossed:

```text
100, 110, 120, 130, 140
```

Each threshold is recorded when first reached.

---

## Team postseason/progression milestones

Required achievements:

```text
POSTSEASON_BERTH
DIVISION_CHAMPION
WILD_CARD_SERIES_WIN
DIVISION_SERIES_WIN
LEAGUE_CHAMPIONSHIP_SERIES_WIN
WORLD_SERIES_WIN
```

The implementation must first identify a deterministic OOTP source for these states/events.

Preferred evidence order:

1. explicit OOTP message/event text with stable team/date/entity references;
2. explicit postseason series metadata in game-box/save files;
3. a validated standings/bracket source;
4. deterministic derivation only if the required series/standings structure has been proven.

Do not infer a division title or postseason berth from vague heuristics.

If a source category is not present in the current sample, report `NOT AVAILABLE IN SAMPLE` rather than fabricating support.

These achievements can occur before or after regular-season finalization as baseball semantics require.

---

## Regular-season completion eligibility

Add a configurable setting:

```text
regular_season_game_target = 162
```

Default is MLB 162.

The "Finalize Regular Season" button becomes enabled when the primary/tracked team's processed regular-season game count reaches the configured target.

Count:

```text
DISTINCT games.game_id
WHERE competition_type = regular_season
AND tracked_team_id IN (home_team_id, away_team_id)
AND season = active_season
```

Do not count spring training or postseason games.

If the app later supports multiple independently tracked teams, finalization state should be team/league aware rather than assuming all teams share one counter.

---

## Finalize Regular Season button flow

Place the button adjacent to the existing/current game-box refresh/import action. If that action is not yet exposed in the final UI, place both in the same compact data-refresh control area rather than inventing a new top-level menu.

Button states:

```text
Disabled: processed regular-season games < configured target
Enabled:  processed regular-season games >= configured target and season not finalized
Finalized: season already finalized; offer details/reconcile action instead of duplicating work
```

On click:

```text
1. Resolve active season + tracked team.
2. Confirm processed regular-season game count.
3. Locate player_*_stats.txt files.
4. Verify they contain the season being finalized.
5. Verify the export is fresh enough to represent the completed season.
6. If invalid/stale/missing:
     - explain that a new OOTP player stats export is recommended;
     - offer Recheck / Browse if appropriate;
     - allow "Continue without export".
7. If valid:
     - parse the authoritative season rows;
     - reconcile app ledger aggregate vs OOTP values;
     - preserve before/after/difference metadata;
     - write finalized season stats;
     - evaluate final rate milestones.
8. Mark regular season finalized.
9. Refresh season views and milestone views.
10. Continue allowing postseason import/achievements.
```

---

## Fresh export validation

A file merely existing is not enough.

A valid final export must at minimum:

- be a recognized `player_*_stats.txt` source;
- contain the season being finalized;
- have a source hash different from an obsolete accepted checkpoint when applicable;
- contain plausible completed-season data rather than clearly lagging behind the processed game ledger.

Use actual source fields to design a deterministic freshness check. Possible evidence includes source modification time relative to the last processed game source and/or comparison of exported G/PA/AB/IP totals against ledger totals.

Do not reject a fresh export merely because reconciliation finds a small discrepancy; discrepancies are the reason reconciliation exists.

If the only file is clearly from a prior season or a stale earlier checkpoint, treat it as no valid export.

---

## Continue without export

The user may explicitly finalize without a valid export.

In that case:

```text
season_status = finalized_unreconciled
```

- preserve all game-ledger counting totals;
- preserve already achieved counting milestones;
- evaluate only rate stats that can be proven accurately from complete ledger components;
- never guess FIP or missing-component rate stats;
- allow a later `Reconcile Finalized Season` action when a fresh export becomes available.

Late reconciliation must not duplicate counting milestones or game milestones.

---

## Reconciliation model

Do not erase the live aggregate without trace.

For every reconciled field preserve enough information to answer:

```text
ledger_value
export_value
adjustment = export_value - ledger_value
source checkpoint
```

OOTP final export becomes the authoritative finalized season value where available.

Example:

```text
H: ledger 181 -> OOTP 182 -> adjustment +1
RBI: ledger 117 -> OOTP 118 -> adjustment +1
AVG: final OOTP .319
```

This allows parser quality audits later.

---

## Suggested storage concepts

Exact migration may adapt to the current schema, but the following concepts are required:

```text
season_states
stats_checkpoints
checkpoint_source_files
player_season_batting
player_season_pitching
team_season_stats
season_stat_reconciliations
season_milestone_achievements
```

`player_season_*` rows should preserve:

```text
player_id
season
competition_type
live/counting values
finalized authoritative values where available
finalization/reconciliation status
```

`season_milestone_achievements` should preserve at least:

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
source = game_crossing | final_export | postseason_event
context/evidence nullable
UNIQUE identity preventing duplicate achievement creation
```

---

## Configurability

Reuse the rule-setting pattern already implemented for game milestones.

At minimum support settings for:

```text
regular_season_game_target (default 162)
batting/pitching season counting threshold lists
batting final rate threshold lists
pitching ERA/FIP bucket enablement
team win threshold list
rate qualification values
```

Defaults must exactly match this document.

Changing a season counting threshold configuration should rebuild season milestone achievements from the existing Game Ledger without reparsing OOTP files.

Changing rate thresholds should reevaluate finalized season rows.

Named postseason achievements remain named predicates/events.

---

## Career handoff

This task prepares career tracking but does not need to finish career milestones.

The preseason/final checkpoints must preserve career totals from OOTP wherever available so the later career system can use:

```text
latest trusted career checkpoint
+ subsequent per-game regular-season deltas
```

A regular-season final export becomes the natural trusted baseline for the next season.
