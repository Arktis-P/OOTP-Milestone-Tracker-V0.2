# Task 003 — All Milestone Ladder Validation

## Context

Remote branch: `user/Workspace`

The milestone visualization has been generalized from the career-hit prototype to every milestone type currently represented by the sample DB. The `Milestones` database table page remains a table by design. The combined ladder is used in Player Records > Milestones so one statistic shows several thresholds on one continuous gauge.

D2Coding remains a CUI fallback only. Do not add or commit font binaries.

## Current ladder catalog

Player career:
- H: 2,000 / 2,500 / 3,000 / 3,500
- HR: 300 / 400 / 500 / 600 / 700
- RBI: 1,000 / 1,250 / 1,500 / 1,750 / 2,000
- G: 1,000 / 1,500 / 2,000 / 2,500 / 3,000
- W: 100 / 150 / 200 / 250 / 300
- SO: 1,000 / 1,500 / 2,000 / 2,500 / 3,000

Player season:
- H: 150 / 175 / 200 / 225 / 250
- HR: 30 / 40 / 50 / 60 / 70
- W: 10 / 15 / 20 / 25 / 30

Player awards:
- ALLSTAR: 5 / 10 / 15 / 20 / 25 selections

Team career catalog is also prepared for later team-detail visualization:
- W: 1,000 / 2,000 / 3,000 / 4,000 / 5,000

These values are prototype display rules, not the final configurable milestone-rules DB.

## Scope

Validation and minimal fixes only.

Do NOT:
- redesign navigation or pages,
- change the DB schema or sample row counts,
- change the Milestones table page into gauges,
- add OOTP parsing,
- implement forecasting,
- add CUI/D2Coding unless explicitly requested,
- push to remote,
- open a PR,
- run GitHub Actions.

## Required checks

### 1. Sync

```powershell
git fetch origin
git status
```

Ensure local `user/Workspace` contains latest remote commit before validation.

### 2. Compile

```powershell
.\.venv\Scripts\python.exe -m compileall -q src scripts
```

Expected: exit code 0.

### 3. Existing tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all existing tests pass. Sample DB row counts must not change.

### 4. GUI smoke

```powershell
.\.venv\Scripts\python.exe scripts\run_dev.py
```

Open `Player Records > Milestones`.

Check `박지호 / Ji-ho Park`:
- Career Hits: one ladder with 2,000 / 2,500 / 3,000 / 3,500.
- Career Home Runs: one ladder with 300 / 400 / 500 / 600 / 700.
- Career RBI: one ladder with 1,000 / 1,250 / 1,500 / 1,750 / 2,000.
- Season Home Runs: one ladder with 30 / 40 / 50 / 60 / 70.
- All-Star Selections: one ladder with 5 / 10 / 15 / 20 / 25.
- No duplicate single-target gauge should appear for those same scope/stat pairs.

Check `김민준 / Min-jun Kim`:
- Career Hits and Career Home Runs ladders render below/around first thresholds correctly.
- Season Hits ladder renders 150 / 175 / 200 / 225 / 250.

Check `이현우 / Hyun-woo Lee`:
- Career Wins ladder renders 100 / 150 / 200 / 250 / 300.
- Career Strikeouts ladder renders 1,000 / 1,500 / 2,000 / 2,500 / 3,000.
- Season Wins ladder renders 10 / 15 / 20 / 25 / 30.

Check `한우진 / Woo-jin Han`:
- Career Games ladder renders 1,000 / 1,500 / 2,000 / 2,500 / 3,000.

### 5. Layout

At minimum app size `920×620`:
- labels remain visible,
- neighboring threshold labels do not overlap materially,
- horizontal gauge stays inside the scrollable content,
- summary text is readable,
- verify both Dark and Light themes.

### 6. Milestones table regression

Open `Milestones` page and confirm:
- it remains a compact sortable/filterable table,
- individual DB milestone rows still appear,
- tracked-team filtering still works.

## Fix policy

Only fix failures caused by the generalized ladder display.

Preferred order:
1. catalog lookup/entity key,
2. grouping/deduplication,
3. painter geometry,
4. label spacing/clamping,
5. palette contrast.

Do not modify milestone thresholds based on personal preference during validation. Report threshold-design concerns separately.

## Git policy

- No changes needed: no empty commit.
- Fix required: one local commit only.
- No push / PR / Actions.

Suggested commit:

```text
fix: validate all milestone ladders
```

## Report format

```text
RESULT: PASS | FAIL

CHECKS
- compile: PASS/FAIL
- tests: PASS/FAIL
- career batting ladders: PASS/FAIL
- career pitching ladders: PASS/FAIL
- season ladders: PASS/FAIL
- award ladder: PASS/FAIL
- career games ladder: PASS/FAIL
- min-size layout: PASS/FAIL
- dark/light: PASS/FAIL
- milestones table regression: PASS/FAIL

FIXES
- NONE
or
- <minimal fixes>

LOCAL COMMITS
- NONE
or
- <hash> <message>

BLOCKERS
- NONE
or
- <exact blocker>
```
