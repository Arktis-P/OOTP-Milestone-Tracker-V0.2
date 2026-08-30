# Milestone Rule System Design

## Goal

Milestone thresholds must not be hard-coded in the UI. The app should let the user choose **what to track**, **where tracking begins**, and **the numeric interval used to register later milestones**.

The final settings UI should support presets/sets and compact slider-style controls, while the stored rule remains data-driven.

## Rule identity

A rule is identified by:

- `entity_type`: `player` / `team`
- `scope`: `game` / `season` / `career` / `award`
- `stat_key`: e.g. `H`, `HR`, `RBI`, `W`, `SO`, `ALLSTAR`

Player and team rules are separate even when they share a stat key. For example player career wins and team career wins use different threshold ranges.

## Threshold modes

### Interval mode

Use when milestones follow a regular sequence.

Example:

```text
Career Hits
start      = 2000
interval   = 500
end        = 3500

=> 2000 / 2500 / 3000 / 3500
```

Recommended stored fields:

```text
mode          interval
start_value   2000
step_value     500
end_value     3500
```

### Explicit mode

Use when milestone values are irregular.

```text
mode        explicit
thresholds  [10, 20, 30, 50]
```

## Common rule fields

```text
id
entity_type
scope
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
preset_id        nullable
```

Later filters can be added separately, such as league/team applicability, active/retired players, or position restrictions. Those filters should not be mixed into the threshold generator itself.

## Registration semantics

A configured threshold becomes a milestone event when an import changes a value across that threshold.

```text
previous value < threshold <= imported current value
```

Example:

```text
Previous snapshot: 1,998 H
Current snapshot : 2,002 H
Threshold        : 2,000 H

=> Register 2,000-hit milestone once.
```

Milestone registration must be idempotent: importing the same save again must not create the same achievement twice.

## Presets / sets

The app should ship with selectable rule sets rather than forcing users to configure every statistic manually.

Proposed presets:

- `Standard`: balanced default milestones.
- `Major only`: only historically significant / high thresholds.
- `Dense`: starts earlier and uses smaller intervals.
- `Custom`: user-edited rules.

A preset is only a collection of milestone-rule definitions. Applying a preset copies/activates the selected rules; users may then override individual rules.

## Planned compact UI

A rule editor can be represented as one compact row/card:

```text
[ON] Career Hits       2,000 ├──────────────┤ 3,500
                       Step [500 ▾]
                       Preview: 2,000 · 2,500 · 3,000 · 3,500
```

For explicit rules:

```text
[ON] Award Count       [ 5 ] [ 10 ] [ 15 ] [ 20 ] [ 25 ]
```

The top of the page can expose preset selection:

```text
Rule Set   [ Standard ▾ ]   [Apply]
```

## Separation from import frequency

Threshold interval and data-import frequency are different concepts.

- Rule interval: e.g. register a career-hit milestone every 500 hits.
- Import frequency: when the app reads the OOTP save again.

Initial implementation should import when the user requests refresh/update. Automatic periodic/background import can be added later without changing milestone rule definitions.
