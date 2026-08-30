# OOTP 27 Data Import Plan

## Core model

The app uses a **baseline + incremental game ledger**.

```text
player_*_stats.txt baseline
        +
automatically created per-game records
        ↓
internal current-state DB
        ↓
milestone evaluation
```

`player_*_stats.txt` is not the routine refresh source. It is a checkpoint/baseline the user can create manually, ideally before a season or whenever reconciliation is needed.

After a baseline, every newly created game file updates the internal DB automatically when the app refreshes/scans the save.

`*_rosters.txt` is not required.

## Sources and responsibilities

### Baseline

`import_export/player_*_stats.txt`

Purpose:
- stable player IDs
- historical/season totals available at checkpoint time
- initialize/reconcile internal aggregates

### Per-game numeric ledger

`news/html/box_scores/game_box_*.html`

Purpose:
- game ID/date/teams/status
- player participation
- batting/pitching line deltas
- authoritative incremental additions after the baseline

### Play context

`news/txt/leagues/log_*.txt`

Purpose:
- exact inning/play sequence
- batter/pitcher counterpart
- score/base/out context
- exact milestone play when resolvable

### Optional corroboration

`messages/message*.txt`

Purpose:
- optional milestone/news corroboration
- entity/date enrichment

## Competition separation

All records must be isolated by:

```text
regular_season
postseason
spring_training
international
```

Season aggregate identity:

```text
player_id + season + competition_type
```

Career aggregate identity:

```text
player_id + competition_type
```

Never merge competition types.

## Ledger pipeline

```text
selected .lg
  -> load active baseline
  -> scan game_box files
  -> identify unprocessed/changed games
  -> parse GameRecord + player game lines
  -> classify competition_type
  -> persist game/game-player rows
  -> apply/rebuild aggregates
  -> evaluate milestones after that game
  -> parse matching log only when context is needed
  -> persist milestone achievement
  -> refresh UI
```

## Baseline checkpoint

A baseline must also record which game files are already represented by the checkpoint.

Recommended baseline metadata:

```text
baseline_id
created_at
save_path
season
source_signature
existing_game_ids snapshot or equivalent cutoff
```

This prevents double counting when a baseline is generated after some games have already been played.

For the expected preseason workflow, the current-season game set is normally empty, but the design must still support midseason reconciliation.

## Canonical storage

Recommended tables/concepts:

### baselines
- checkpoint metadata
- source signatures
- cutoff/known game IDs

### games
- `game_id` unique
- game date
- season
- competition type
- home/away teams
- score/status
- source hash

### game_player_batting
- one row per game/player batting line

### game_player_pitching
- one row per game/player pitching line

### batting_seasons / pitching_seasons
- fast current-state aggregates
- key includes competition type

### milestone_achievements
- threshold crossed during a specific processed game
- references `game_id`
- optional exact play context from log

## Idempotency and corrections

Processing the same unchanged `game_id` twice must not add stats twice.

Recommended behavior:

```text
new game_id
  -> parse + insert + aggregate

existing game_id + same hash
  -> skip

existing game_id + changed hash
  -> replace game rows
  -> rebuild affected player/season/competition aggregates from baseline + stored games
```

Prefer a rebuild of the affected slice over fragile manual subtraction when corrected/replayed files are detected.

## Milestone timing advantage

Because stats are applied one game at a time, threshold crossing is detected on the exact game:

```text
before game: 2,998 H
game delta : +3 H
after game : 3,001 H

=> 3,000 H achieved in this game
```

The matching play log can then identify which of the three hits was the 3,000th hit and capture opponent pitcher, inning, score, outs, base state, and play text when possible.

## Game count

Player game number is derived from processed participation records, not guessed from team games.

Season milestone game number:

```text
count player appearances
where season + competition_type match
through achievement game
```

Career milestone game number:

```text
baseline career games
+ processed appearances after baseline
within competition_type
```

## Forecasting

Forecasting remains intentionally small in scope: only whether the next milestone is likely to be reached in the current season.

Once game-ledger tracking exists, the estimator can use current per-game pace and remaining games when the remaining schedule is known. Otherwise return `Unknown`.

Do not predict a future career year.

## Development order

1. Deep-research actual game-box/log formats.
2. Implement game parsers and competition classifier.
3. Implement baseline import/checkpoint.
4. Implement game ledger + idempotent incremental aggregation.
5. Evaluate milestones immediately after each game delta.
6. Resolve exact milestone play from log.
7. Add reconciliation via a later manually generated stats baseline.
8. Add current-season likely/unlikely forecast.
