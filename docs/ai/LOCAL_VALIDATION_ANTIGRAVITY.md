# Local Validation Handoff — Antigravity

## Worker selection

- Primary: Gemini 3.6 Flash
- Fallback: Gemini 3.5 Flash
- Purpose: cheap local execution/verification, not redesign or feature expansion.

## Context already decided — do not re-investigate

Repository: `Arktis-P/OOTP-Milestone-Tracker-V0.2`
Branch: `user/Workspace`
Stack: Python 3.11+ / PySide6 / SQLite.
Architecture and intended behavior are in `README.md` and `docs/ARCHITECTURE.md`.
The runtime DB is generated from `src/ootp_milestone_tracker/db/sample_seed.py`.
No OOTP parser exists yet; this task validates only the sample DB viewer.

Git/GitHub cost rule:
- CHECKPOINT = LOCAL COMMIT
- FEATURE COMPLETE = one eventual PUSH by the top-level/user workflow
- No PR, no GitHub Actions, no remote CI, no remote push from this worker.

## Task

Validate the current branch locally and fix only defects required for the sample DB viewer to run correctly.

### 1. Environment

From repository root on Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

If an existing valid `.venv` is present, reuse it instead of reinstalling.

### 2. Cheap static gate

Run:

```powershell
python -m compileall -q src scripts
python -c "from ootp_milestone_tracker.db.database import Database; from ootp_milestone_tracker.core.paths import DEFAULT_DB_PATH; db=Database(DEFAULT_DB_PATH); db.reset_sample(); print(DEFAULT_DB_PATH)"
```

Then inspect SQLite cheaply:

```powershell
python -c "from ootp_milestone_tracker.db.database import Database; from ootp_milestone_tracker.db.repository import Repository; from ootp_milestone_tracker.core.paths import DEFAULT_DB_PATH; r=Repository(Database(DEFAULT_DB_PATH)); print(r.dashboard_summary()); print(len(r.players()), len(r.milestones()))"
```

Expected broad result:
- DB initializes without exception.
- 3 teams / 8 players in seed data.
- tracked team is `Seoul Meteors`.
- tracked-team milestone query returns rows.

Do not spend tokens comparing every sample number unless a UI/query defect points there.

### 3. GUI smoke test

Run:

```powershell
python scripts/run_dev.py
```

Check only these acceptance points:

1. App opens at roughly 1180×760 and remains usable down to 920×620.
2. Sidebar has Dashboard / Milestones / Player Records / Tools / Settings.
3. Dashboard displays Seoul Meteors summary and milestone rows.
4. Milestones defaults to tracked-team-only and search/scope/team-visibility filters update the table.
5. Player Records lists tracked-team players first with `★`; selecting batter/pitcher changes the season table and milestone gauges.
6. Settings can switch tracked team, edit Korean display name, change Dark/Light theme, and refresh visible pages.
7. Tools → reset sample DB recreates the DB without crashing.
8. Save-folder browse dialog opens; no actual OOTP import is expected.

Visual goal: compact modern data tool. Do not redesign based on personal preference. Only fix clear clipping, unreadable contrast, broken layout, or unusable sizing.

### 4. Tests

Only after the smoke test works, add a minimal pytest suite if useful. Prioritize:
- DB initialization/seed count
- tracked-team milestone filtering
- team switch behavior
- player name mapping persistence

Do not add screenshot tests, full Qt automation, coverage tooling, or CI in this pass.

### 5. Repair rules

- Prefer the smallest local patch.
- Do not change schema or directory architecture unless the app cannot run otherwise.
- Do not add dependencies unless absolutely required.
- Do not implement the OOTP parser, forecasting, or new UI features.
- If PySide6 API behavior differs by installed version, make the smallest compatible fix and note it.

### 6. Git handling

After successful validation:

```powershell
git status
git diff --check
```

If you changed files, create local commits only. Suggested message:

```text
fix: validate sample database viewer locally
```

DO NOT PUSH.

## Required report — keep concise

Return exactly these sections:

```text
RESULT: PASS | PASS_WITH_FIXES | FAIL

CHECKS
- compile: PASS/FAIL
- db seed/query: PASS/FAIL
- GUI smoke: PASS/FAIL
- settings persistence: PASS/FAIL
- tests: PASS/FAIL/SKIPPED

FIXES
- <only files + reason; NONE if unchanged>

LOCAL COMMITS
- <sha message; NONE if unchanged>

BLOCKERS
- <only actionable blockers; NONE if none>
```

Do not repeat architecture or summarize source files unless needed to explain a failure.
