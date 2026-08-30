# OOTP 27 Local Data Import Plan

## Source location

Do not hard-code a Windows username or a localized `Documents` folder name. Resolve the current Windows Documents known folder, then append:

```text
Out of the Park Developments/OOTP Baseball 27/saved_games
```

Each save is a directory ending in `.lg`. Settings may override auto-detection.

## Routine import source

The routine importer must use `import_export/player_*_stats.txt` as the authoritative day-to-day source.

Reason: the user can export these files from OOTP with one action. `*_rosters.txt` requires repeated league selection and must not be required for normal refresh/import.

`*_rosters.txt` is therefore research/fallback-only and must not be a dependency of Importer v1.

## Supporting event sources

These sources are not the authoritative numeric stat source. They are used later to resolve the exact game/play context when a milestone threshold was crossed:

```text
messages/message*.txt
news/html/box_scores/game_box_*.html
news/txt/leagues/log_*.txt
```

Source responsibilities:

- `player_*_stats.txt`: player identity available in the file, team/league keys when available, season/stat totals, career totals derived from season rows where appropriate.
- `game_box_*.html`: game ID, date, teams, player participation, game-level lines.
- `log_*.txt`: play-by-play / game situation, opponent player when identifiable, inning/score/base-out context when present.
- `message*.txt`: optional cross-check and entity/date enrichment; never required to recognize a custom threshold.

## Competition type is mandatory

All season and career tracking must be separated by competition type from the first real import.

Canonical values:

```text
regular_season
postseason
spring_training
international
```

Do not merge these into one season total.

The local worker must determine how each `player_*_stats.txt` family identifies the competition type (file name, directory, fields, or export category) and document the exact mapping. If an exported family cannot be mapped safely, report it instead of guessing.

Current-state season identity must include at least:

```text
player_id + season + competition_type
```

Career totals are also calculated independently per `competition_type`.

## Import pipeline

```text
.lg save
  -> source locator
  -> player stats discovery
  -> player stats parser
  -> competition-type mapping
  -> normalized records
  -> SQLite current state UPSERT
  -> stat snapshot
  -> milestone threshold evaluation
  -> optional event resolver (box/log/messages)
  -> UI refresh
```

## Stable identity

Use OOTP IDs, never player names, as identities.

Primary identity confirmed locally:

```text
player_id
```

Secondary keys include `team_id`, `game_id`, and `year` when supplied by the source.

Because roster export is no longer required, Importer v1 must derive every routinely required identity/display field from `player_*_stats.txt` or retain a documented nullable/default value. It must never silently fall back to roster files.

## Snapshot requirement

Every materially changed import should append snapshot metadata sufficient to detect threshold crossing:

```text
previous < threshold <= current
```

Snapshot identity must include:

```text
entity_type
entity_id
scope
competition_type
season nullable
stat_key
value
```

Repeated import of unchanged source data must not create duplicate snapshots or milestone achievements.

## Milestone achievement context

A threshold crossing is first detected from stats snapshots. The exact achievement event may then be enriched from game sources.

Desired event fields are defined in `docs/MILESTONE_ACHIEVEMENT_MODEL.md`.

A numeric crossing can exist temporarily with unresolved game context. Context enrichment must be idempotent and may fill nullable fields later.

## Forecast scope

Forecasting is intentionally small: only answer whether the next milestone is plausibly reachable during the current season.

Do not build multi-year career forecasts.

A forecast should use current-season pace and known/estimated remaining schedule only when enough data exists. If remaining schedule cannot be determined safely, return `unknown` rather than fabricate precision.

## Safety

The importer is read-only with respect to OOTP saves.

- Never edit/delete/move files inside `.lg`.
- Never commit raw save contents.
- Keep source-specific parsing out of UI/Repository code.
- Do not require roster export for routine use.
