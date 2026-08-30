# OOTP Milestone Tracker V0.2

A compact local database viewer and milestone tracker for OOTP save data.

This branch starts the application from a clean architecture. The current implementation uses generated sample data so the UI and local database workflow can be validated before an OOTP save parser is connected.

## Stack

- Python 3.11+
- PySide6 / Qt
- SQLite (Python standard library)
- Optional PyInstaller for Windows builds

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python scripts/run_dev.py
```

The first launch creates `data/runtime/tracker.db` and seeds it with fictional sample data.

## Repository layout

```text
src/                         Application source
  ootp_milestone_tracker/
    db/                      SQLite schema, sample seed, repositories
    ui/                      Main window, pages, reusable widgets, theme
    core/                    Paths and app-level helpers

data/
  samples/ootp_save/         Raw OOTP save/export samples for parser research
  runtime/                   Local generated SQLite DB (ignored)

scripts/                     Development/build/maintenance scripts
artifacts/builds/             Packaged executables and build output (ignored)
docs/                         Architecture and AI/local-worker instructions
tests/                        Local-worker verification/tests
```

## Current scope

- Compact five-section shell: Dashboard / Milestones / Player Records / Tools / Settings
- SQLite sample DB initialization
- Tracked-team-first player browsing
- Milestone table with search/filtering
- Player current-season/history/career summary and milestone gauges
- Save-folder, tracked-team, appearance, and English→Korean name mapping settings
- Development tools placeholder and DB folder access

## Workflow rule

Remote work should batch repository writes into a feature-complete commit and update the branch once. Runtime tests, GUI smoke tests, packaging verification, and environment-specific checks are delegated to a local worker. See `docs/ai/LOCAL_VALIDATION_ANTIGRAVITY.md`.
