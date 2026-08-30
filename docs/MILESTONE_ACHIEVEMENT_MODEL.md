# Milestone Achievement Model

## Purpose

A milestone achievement is detected **while applying one game's stat delta** to the internal ledger. This makes the achievement game exact by construction instead of inferring it later from two distant aggregate snapshots.

## Detection flow

```text
baseline total
  + processed games in order
  -> before-game value
  -> apply current game delta
  -> after-game value
  -> previous < threshold <= current
  -> achievement belongs to current game
```

Example:

```text
Before game : 2,998 H
Game        : 3-for-4
After game  : 3,001 H
Threshold   : 3,000 H

=> 3,000th hit occurred in this game
```

The matching play-by-play log can then determine which hit was the threshold play.

## Achievement identity

At minimum:

```text
rule_id
entity_id
competition_type
season nullable
threshold_value
```

The same achievement must never be inserted twice.

## Required fields

Recommended `milestone_achievements` fields:

```text
id
rule_id
entity_type
entity_id
scope
competition_type
season nullable
stat_key
threshold_value
value_before
value_after
game_id
game_date
player_game_number nullable
team_game_number nullable
resolution_status
```

`resolution_status`:

```text
game_resolved
play_resolved
manual
```

With a game-ledger pipeline there should normally be no numeric `unresolved` state: the crossing game is already known. Only the exact play may remain unresolved.

## Exact play context

Store when safely resolved from the log:

```text
play_sequence nullable
inning nullable
inning_half nullable
team_id nullable
opponent_team_id nullable
opponent_player_id nullable
score_for nullable
score_against nullable
outs nullable
base_state nullable
play_result nullable
context_text nullable
source_file nullable
```

Do not fabricate unavailable context.

## Competition separation

Every achievement belongs to one canonical competition type:

```text
regular_season
postseason
spring_training
international
```

Career and season values, player game counts, and milestone rules are all evaluated independently inside that competition type.

## Game count semantics

Season milestone:

```text
player appearances through achievement game
within season + competition_type
```

Career milestone:

```text
baseline career game count
+ post-baseline player appearances through achievement game
within competition_type
```

## Source responsibility

1. `player_*_stats.txt`: baseline/checkpoint and reconciliation.
2. `game_box_*.html`: authoritative per-game numeric deltas and achievement game.
3. `log_*.txt`: exact threshold play and opponent/situation context.
4. `message*.txt`: optional corroboration/enrichment.

## Multiple stat increments in one game

If a player jumps across multiple configured thresholds in one game, register each crossed threshold separately but reference the same game.

If the same stat increases multiple times in one game (for example three hits), the play log must walk the relevant events in sequence starting from the before-game value to find the exact threshold event.

Example:

```text
before game = 2,998
hit #1 -> 2,999
hit #2 -> 3,000  <- achievement play
hit #3 -> 3,001
```

## Display example

```text
3,000 Career Hits · Regular Season
2034-08-17 vs Busan Waves
Career Game 2,184
7th inning · 1 out · tied 3-3
Single off Pitcher Name
```

Only display context fields actually resolved from source data.
