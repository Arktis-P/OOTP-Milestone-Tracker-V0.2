# Architecture

## Goal

Keep the UI independent from OOTP save-file parsing. The application reads only its own normalized SQLite database. A future importer will translate OOTP save/export data into that database.

```text
OOTP save/export files
        ↓
Importer / Parser        (future)
        ↓
Normalized SQLite DB     data/runtime/tracker.db
        ↓
Repository queries
        ↓
PySide6 UI
```

## Boundaries

### `src/ootp_milestone_tracker/db`
Owns the application schema, generated sample seed data, and query/update methods. OOTP-specific parsing rules must not leak into UI pages.

### `src/ootp_milestone_tracker/ui`
Owns the compact desktop shell and presentation. Pages consume dictionaries returned by `Repository`; they should not issue raw SQL.

### `data/samples/ootp_save`
Reserved for real save/export fragments used to research and reproduce OOTP parsing. Local files are ignored by Git by default. Add only deliberately sanitized fixtures when they become stable test assets.

### `data/runtime`
Generated local application data. Never treat this as source-of-truth in Git.

### `scripts`
Small deterministic entry points for development, DB reset, packaging, migrations, or import experiments. Long-lived business logic belongs in `src/`.

### `artifacts/builds`
Local executable/package output. Not source-controlled.

### `docs`
Architecture, data-format notes, operating rules, and AI handoff instructions.

### `tests`
Local verification suite. Remote agents may prepare implementation, but environment/UI execution and validation are delegated to local workers under the project cost rule.

## Current schema

- `teams`: team identity and tracked-team flag
- `players`: player identity, team, display-name mapping, position, age
- `batting_seasons`: normalized batting season rows
- `pitching_seasons`: normalized pitching season rows
- `awards`: player award history
- `milestones`: player/team, game/season/career/award milestone rows
- `app_settings`: local application preferences

## Design constraints

1. SQLite is the app database, not an OOTP mirror.
2. External OOTP identifiers should become stable primary/foreign keys once the parser is connected.
3. Name mapping is keyed by player ID; translated strings are presentation data.
4. Tracked-team filtering belongs in repository queries, not duplicated across pages.
5. Milestone forecast logic should later be a separate service layer rather than embedded in widgets.
6. Raw save samples, runtime DBs, and build artifacts remain outside normal source control.
