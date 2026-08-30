# Milestone Rule System Design

## Goal

Milestones are data-driven. The user chooses what to track, where tracking starts, how often later thresholds are registered, and which competition type the rule applies to.

The final UI should expose compact presets/sets plus per-rule controls instead of forcing manual entry for every threshold.

## Rule identity

A rule is identified by:

```text
entity_type
scope
competition_type
stat_key
```

Canonical values:

- `entity_type`: `player` / `team`
- `scope`: `game` / `season` / `career` / `award`
- `competition_type`: `regular_season` / `postseason` / `spring_training` / `international`
- `stat_key`: `H`, `HR`, `RBI`, `W`, `SO`, etc.

Competition types must never share accumulated totals. Example: regular-season career hits and postseason career hits are different tracked series.

## Threshold modes

### Interval

```text
Career Hits / Regular Season
start    = 2000
interval = 500
end      = 3500

=> 2000 / 2500 / 3000 / 3500
```

### Explicit

For irregular thresholds:

```text
thresholds = [10, 20, 30, 50]
```

## Common fields

```text
id
entity_type
scope
competition_type
stat_key
title
enabled
mode
start_value
step_value
end_value
explicit_thresholds
unit
sort_order
preset_id nullable
```

## Registration semantics

A configured threshold becomes an achievement when:

```text
previous value < threshold <= current value
```

The comparison must occur within the same `competition_type` and, for season rules, the same season.

Achievement registration is idempotent.

## Presets / sets

Initial concept:

- `Standard`
- `Major only`
- `Dense`
- `Custom`

A preset is a collection of rule definitions. Users can apply a preset and override individual rules.

Planned compact editor:

```text
[ON] Career Hits   [Regular Season ▾]
     2,000 ├──────────────┤ 3,500   Step [500 ▾]
     Preview: 2,000 · 2,500 · 3,000 · 3,500
```

## Import frequency is separate

Threshold interval and import frequency are unrelated.

- Threshold interval: how often a stat becomes a milestone.
- Import frequency: when the app rereads OOTP data.

Initial operation is manual `Import / Refresh`. Periodic refresh may be added later.

## Achievement context

The milestone rule decides **what counts**. A separate achievement record stores **when/how it happened**.

See `docs/MILESTONE_ACHIEVEMENT_MODEL.md`.

Required design principle:

- `player_*_stats.txt` determines the authoritative numeric crossing.
- game box/log/message sources enrich the crossing with exact game context where available.

## Forecasting

Forecasting is deliberately limited to the next threshold in the current season.

Possible display states:

```text
Likely this season
Unlikely this season
Already achieved
Unknown
```

Do not predict a specific future career year.

A basic estimator may compare:

```text
remaining_to_target
current_season_stat_per_game
remaining_games
```

Only produce Likely/Unlikely when remaining-games information is reliable enough. Otherwise return `Unknown`.

For contexts with inherently variable schedules (especially postseason/international), `Unknown` is acceptable unless a remaining schedule is known.
