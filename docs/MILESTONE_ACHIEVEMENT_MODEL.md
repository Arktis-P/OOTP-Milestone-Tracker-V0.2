# Milestone Achievement Model

## Purpose

A milestone achievement must preserve both the threshold crossing and, when available, the exact game context in which it happened.

The numeric source of truth is the imported player-stat total. Game/message sources enrich that crossing with evidence and presentation details.

## Achievement identity

At minimum, one achievement is uniquely identified by:

```text
rule_id
entity_id
competition_type
season nullable
threshold_value
```

The same threshold must not be registered twice after repeated imports.

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
achieved_at nullable
import_run_id
resolution_status
```

`resolution_status`:

```text
unresolved
resolved_game
resolved_play
manual
```

## Game context fields

Store these when they can be resolved safely:

```text
game_id nullable
game_date nullable
team_id nullable
opponent_team_id nullable
opponent_player_id nullable
player_game_number nullable
team_game_number nullable
inning nullable
inning_half nullable
score_for nullable
score_against nullable
outs nullable
base_state nullable
play_result nullable
context_text nullable
source_file nullable
```

Interpretation:

- `game_date`: in-game date of the achievement.
- `game_id`: OOTP game identity.
- `opponent_player_id`: batter/pitcher counterpart when meaningful and discoverable.
- `player_game_number`: player's game count at the moment. For a career milestone this should represent the career game count within the same competition type; for a season milestone it should represent that season's game count within the same competition type.
- `team_game_number`: optional team game number when available.
- `inning`, `score`, `outs`, `base_state`: game situation when the log can resolve the exact play.
- `play_result` / `context_text`: compact human-readable achievement situation.

Do not fabricate fields that cannot be resolved.

## Competition separation

Every achievement belongs to exactly one canonical competition type:

```text
regular_season
postseason
spring_training
international
```

Career and season game counts are computed independently inside that competition type.

## Resolution flow

```text
stats import
  -> threshold crossing detected
  -> unresolved milestone achievement created
  -> candidate games located between previous/current snapshots
  -> game box narrows game/date/player participation
  -> play log resolves exact play/opponent/situation when possible
  -> message source optionally cross-checks/enriches
  -> achievement marked resolved_game or resolved_play
```

If several games occurred between imports and the exact game cannot be identified, keep the achievement unresolved rather than guessing.

## Source priority

1. `player_*_stats.txt`: authoritative numeric value/crossing.
2. `game_box_*.html`: game/date/team/player/game-line evidence.
3. `log_*.txt`: exact play and opponent/situation evidence.
4. `message*.txt`: optional text/date/entity corroboration.

## Display example

```text
3,000 Career Hits · Regular Season
2034-08-17 vs Busan Waves
Career Game 2,184
7th inning · 1 out · tied 3-3
Single off Pitcher Name
```

Only display fields that were actually resolved.
