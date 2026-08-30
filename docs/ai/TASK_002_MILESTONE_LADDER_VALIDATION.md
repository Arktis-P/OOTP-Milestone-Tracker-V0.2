# Task 002 — Milestone Ladder GUI Validation

## Context

Remote branch: `user/Workspace`

This task validates the first multi-threshold milestone gauge. The GUI now renders career hit milestones on one continuous bar rather than one progress bar per target.

Current prototype rule:

- Career hits (`career` + `H`)
- Thresholds: `2,000 / 2,500 / 3,000 / 3,500`
- Current value comes from the existing milestone DB row.
- No DB schema or sample-count change is intended.
- Other milestone types keep the existing single-target gauge.

D2Coding is reserved for a later CUI fallback. Do not add or commit font binaries in this task.

## Scope

Validation and minimal fixes only.

Do NOT:

- redesign the app,
- change the DB schema,
- add OOTP parsing,
- implement forecasting,
- introduce a CUI fallback unless explicitly requested,
- push to remote,
- open a PR,
- run GitHub Actions.

## Required checks

Run in this order and stop to fix only when a check fails.

### 1. Sync

```powershell
git fetch origin
git status
```

Ensure the local branch contains the latest `origin/user/Workspace` before validating.

### 2. Static compile

```powershell
.\.venv\Scripts\python.exe -m compileall -q src scripts
```

Expected: exit code 0.

### 3. Existing unit tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all existing tests pass. The milestone seed count must not change because this GUI prototype does not modify sample data.

### 4. GUI smoke

```powershell
.\.venv\Scripts\python.exe scripts\run_dev.py
```

Open `Player Records` and select `박지호 / Ji-ho Park`.

In the `Milestones` tab confirm:

1. Career Hits appears exactly once as a combined gauge.
2. One bar contains markers for `2,000`, `2,500`, `3,000`, `3,500`.
3. Current value is `2,431 H`.
4. The summary indicates `69 to 2,500`.
5. `2,000` is visually in the achieved/accent state.
6. `2,500`, `3,000`, `3,500` remain pending.
7. Career HR, RBI, season HR, awards etc. continue to use the previous single-target gauge.
8. At minimum window size `920×620`, threshold labels do not overlap, clip, or leave the visible area.
9. Repeat the gauge visibility check in both Dark and Light themes.

Also select `김민준 / Min-jun Kim` and confirm the same hit ladder can render a current value below 2,000 without exception.

## Fix policy

Only fix issues directly required for the checks above.

Preferred fix order:

1. painter geometry / label clamping,
2. widget minimum height / layout spacing,
3. palette contrast,
4. milestone grouping logic.

If the custom GUI gauge cannot be made readable without a larger redesign, do not implement CUI yet. Report the problem and the exact visual symptom. The planned fallback font is D2Coding.

## Git policy

- If no source fix is needed: do not create an empty commit.
- If a fix is needed: create one local commit only.
- Do not push.
- Do not create a PR.

Suggested commit when needed:

```text
fix: validate milestone ladder gauge
```

## Report format

```text
RESULT: PASS | FAIL

CHECKS
- compile: PASS/FAIL
- tests: PASS/FAIL
- ladder / Ji-ho Park: PASS/FAIL
- ladder / Min-jun Kim: PASS/FAIL
- min-size layout: PASS/FAIL
- dark/light: PASS/FAIL

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
