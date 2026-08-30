# OOTP 27 Local Data Import Plan

## Source location

Do not hard-code a Windows username or a localized `Documents` folder name.

The app resolves the Windows Documents path from the user's shell-folder configuration, then appends:

```text
Out of the Park Developments/OOTP Baseball 27/saved_games
```

This supports ordinary Documents folders and redirected OneDrive Documents folders. Each league save is a directory ending in `.lg`.

The user can always override auto-detection in Settings.

## Initial source file families

The first importer research targets the source families supplied for this project:

```text
*_rosters.txt
player_*_stats.txt
message*.txt
game_box_*.html
log_*.txt
```

These files may live in subdirectories, so discovery is recursive inside the selected `.lg` directory.

## Import pipeline

```text
.lg save directory
  -> source locator
  -> source inventory/scanner
  -> format-specific parsers
  -> normalized import records
  -> import snapshot
  -> SQLite upsert
  -> milestone evaluation
  -> UI refresh
```

## Parser boundaries

Use a separate parser for each source family. Do not let UI or SQLite code parse raw OOTP text/HTML directly.

Expected modules after local format research:

```text
importer/parsers/rosters.py
importer/parsers/player_stats.py
importer/parsers/messages.py
importer/parsers/game_box.py
importer/parsers/logs.py
```

Each parser should return normalized Python records. A later persistence layer decides how those records map to SQLite.

## Stable identity first

Before implementing milestone detection, identify the stable IDs used by the source files for:

- player
- team
- league
- game
- season/date

English player names must never be used as the primary identity because display-name mapping and duplicate names make strings unsafe identifiers.

## Snapshot requirement

Every successful import should create metadata such as:

```text
source_save
imported_at
in_game_date / season when discoverable
source file timestamps or digest
```

Snapshots are necessary to detect a threshold crossing:

```text
previous < milestone <= current
```

and to avoid duplicate milestone events when the same save is imported repeatedly.

## Safety

The importer is read-only with respect to OOTP saves.

- Never edit/delete files inside `.lg`.
- Never move a live save.
- Raw saves remain ignored by Git.
- Research reports should describe formats and schemas rather than commit full personal save contents.

## Current implementation

`source_locator.py` discovers OOTP 27 `.lg` saves.

`source_scanner.py` inventories the five initial file families without reading/changing their contents.

`scripts/inventory_ootp_save.py` is the local entry point for source research.

Actual format parsers must be implemented only after a local worker inspects representative real files and records their structure.
