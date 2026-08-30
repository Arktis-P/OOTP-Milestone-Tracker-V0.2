# Game Milestone Catalog

## Purpose

This document is the canonical catalog for game-level milestones. The evaluator must keep the highest qualifying milestone within the same threshold/hierarchy family instead of recording every lower achievement in the same game.

## Highest-only rule

For threshold ladders, evaluate all configured thresholds but persist only the highest threshold reached by that player/team in the game.

Examples:

```text
5 H  -> GAME_HITS_5 only; do not also store GAME_HITS_4
17 SO -> GAME_STRIKEOUTS_15 only; do not also store GAME_STRIKEOUTS_10
6 HR -> highest configured HR milestone (5 HR) with achieved_value=6
```

Keep the actual game value separately from the milestone threshold.

Special achievements that are logically nested also use highest-only semantics inside their hierarchy.

Pitcher hierarchy:

```text
PERFECT_GAME
  > NO_HIT_NO_RUN
  > SHUTOUT_WIN
  > COMPLETE_GAME_WIN
```

Team pitching hierarchy:

```text
TEAM_PERFECT_GAME
  > TEAM_NO_HIT_NO_RUN
  > TEAM_SHUTOUT_WIN
```

A perfect game therefore must not create separate lower pitching achievements for the same pitcher/team in the same game. Independent achievements such as 15 strikeouts may still coexist with a perfect game.

## Batter thresholds

### Hits

Thresholds:

```text
4 / 5 / 6 / 7
```

Source: upper batting table `H` after its GAME_DELTA semantics have been verified.

Rule family key: `GAME_HITS`.

### RBI

Thresholds:

```text
5 / 6 / 7 / 8 / 9 / 10
```

Source: upper batting table `RBI` only if confirmed GAME_DELTA.

Rule family key: `GAME_RBI`.

### Home runs

Thresholds:

```text
2 / 3 / 4 / 5
```

Do not use the upper batting-table HR column as a game delta. It is a season total in the inspected OOTP 27 source.

Authoritative game occurrence source: lower batting summary `Home Runs:` entries. Preserve when available:

- batter ID
- pitcher ID
- occurrence count in this game
- season home-run number
- contextual text / inning or situation information

Rule family key: `GAME_HR`.

### Stolen bases

Thresholds:

```text
3 / 4 / 5 / 6 / 7
```

Do not use the upper batting-table SB column as a game delta. It is a season total in the inspected source.

Authoritative game occurrence source: lower batting summary `Stolen Bases:` entries.

Rule family key: `GAME_SB`.

### Grand slam

Named predicate: `GAME_GRAND_SLAM`.

A home run must be verified as occurring with the bases loaded before the play. Prefer stable player IDs and deterministic base-state/play evidence. The lower HR summary may provide useful contextual evidence; use the play log when required to prove bases loaded.

Multiple grand slams in one game still create one game-milestone achievement for the rule; preserve occurrence count/details separately if available.

### Cycling hit / hit for the cycle

Named predicate: `GAME_CYCLE`.

The batter must record at least one of each in the same game:

```text
1B + 2B + 3B + HR
```

Sources:

- total `H`: verified game-delta field
- `2B`: lower `Doubles:` summary
- `3B`: lower `Triples:` summary
- `HR`: lower `Home Runs:` summary
- `1B = H - 2B - 3B - HR` only when all source components are trustworthy; otherwise verify via play log events.

## Pitcher milestones

### Strikeouts

Thresholds:

```text
10 / 15 / 20 / 25 / 30
```

Source: pitcher game line `SO`.

Rule family key: `GAME_STRIKEOUTS`.

### Complete-game win

Named predicate: `GAME_COMPLETE_GAME_WIN`.

Required:

- one pitcher accounts for all defensive outs recorded by his team in the game;
- that pitcher is credited with the win.

Handle shortened/extra-inning games using actual team defensive outs, not a hard-coded 27-outs assumption.

### Shutout win

Named predicate: `GAME_SHUTOUT_WIN`.

Required:

- complete-game condition;
- pitcher credited with the win;
- opponent scores 0 runs.

### No-hit no-run

Named predicate: `GAME_NO_HIT_NO_RUN`.

For this project, "노히트 노런" means:

- complete-game condition;
- pitcher credited with the win;
- opponent records 0 hits;
- opponent scores 0 runs.

Do not silently weaken this to a generic no-hitter that allows runs.

### Perfect game

Named predicate: `GAME_PERFECT_GAME`.

Required:

- complete-game condition;
- pitcher credited with the win;
- no opposing batter reaches base by any route that the source can establish (hits, walks, HBP, errors, catcher interference, etc.).

If the available game-box/log evidence cannot prove that no batter reached base, return unsupported/unresolved rather than guessing.

## Team milestones

### Starting lineup all hit

Candidate key: `TEAM_STARTERS_ALL_HIT`.

Every starting batter must record at least one hit. The parser/evaluator must prove which players were starters; substitutes do not alter this predicate.

### All appearing batters hit

Candidate key: `TEAM_APPEARED_ALL_HIT`.

Every batter who appeared for the team in the game must record at least one hit. This is intentionally stricter than the starting-lineup rule.

### Starting lineup all record RBI

Candidate key: `TEAM_STARTERS_ALL_RBI`.

Every starting batter must record at least one RBI.

### All appearing batters record RBI

Candidate key: `TEAM_APPEARED_ALL_RBI`.

Every batter who appeared must record at least one RBI.

The two starter/all-appearance variants are kept distinct because OOTP substitutions make them semantically different. They may later be exposed as separate configurable rules.

### Team shutout win

Key: `TEAM_SHUTOUT_WIN`.

Required:

- team wins;
- opponent scores 0 runs.

This may be achieved by one or multiple pitchers.

### Team no-hit no-run

Key: `TEAM_NO_HIT_NO_RUN`.

Required:

- team wins;
- opponent records 0 hits;
- opponent scores 0 runs.

This is a team predicate and may include a combined pitching performance.

### Team perfect game

Key: `TEAM_PERFECT_GAME`.

Required:

- team wins;
- no opposing batter reaches base by any route supported by the parsed evidence.

This is evaluated on the entire team pitching/defense result, independent of how many pitchers appeared.

## Coexistence rules

Independent families may coexist in the same game.

Example:

```text
Player A: 6 H, 3 HR, cycle
-> GAME_HITS_6
-> GAME_HR_3
-> GAME_CYCLE
```

Do not suppress unrelated achievements merely because one is more prestigious.

Only suppress lower entries within the same threshold family or explicitly nested pitching hierarchy.

## Required persisted values

Each achievement should preserve at least:

```text
game_id
player_id or team_id
rule_key
rule_family
threshold_value nullable
achieved_value nullable
competition_type
game_date
context / evidence fields when available
```

A UNIQUE identity must prevent repeated processing of the same game from duplicating the achievement.
