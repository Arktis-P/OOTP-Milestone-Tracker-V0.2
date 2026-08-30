# Task 008 — Game Milestone Semantic Audit

## Goal

Before closing game-milestone development and moving to season/career tracking, verify that the implemented rules match the intended baseball semantics and do not produce systematic false positives.

This is a narrow audit task. Do not expand into season/career milestone implementation.

## Current state

Previous local work reports:

- exhaustive scan: 7,682 games, 0 parse failures
- full threshold families implemented
- batter/pitcher/team special rules implemented
- highest-only suppression implemented
- 14 tests passing
- local feature commit: `b5ac8bd feat: complete game milestone coverage`

Preserve that work.

## Audit A — Grand Slam false-positive check

The real-save scan reported 651 `GAME_GRAND_SLAM` achievements in 7,682 games. This frequency is high enough to require source-level validation.

### Required checks

1. Randomly sample at least 20 detected grand slams across different games/players.
2. Open the actual lower `Home Runs:` summary text and corresponding play log where useful.
3. Confirm that the matched `3 on` unambiguously means **three runners on base before the home run**.
4. Confirm the parser associates the `3 on` fragment with the correct home-run event/player and does not match unrelated text elsewhere in the summary.
5. Sample at least 20 ordinary home runs that are NOT classified as grand slams and confirm no false negatives caused by formatting variants.
6. Report observed raw text patterns. Do not commit personal/full source files.

If any false positives/negatives are found, fix the parser/evaluator and rerun the full-save scan.

## Audit B — Perfect game proof

A perfect game must mean that **no opposing batter reaches base for any reason** while one pitcher completes the game.

Do not prove perfection using only:

- H = 0
- R = 0
- BB = 0

### Preferred deterministic proof

Use the strongest reliable combination available from OOTP sources. For example, if valid for the format:

```text
pitcher completes all defensive outs
AND batters_faced == defensive_outs
```

For a normal 9-inning game this is 27 BF / 27 outs. For extra/short games, use actual required defensive outs rather than hard-coded 27.

Also inspect whether the source exposes or allows detection of:

- HBP
- reach on error
- catcher interference
- dropped third strike / other non-hit reach
- any other baserunner event

The two real positive samples previously reported must be manually inspected against box/log evidence.

Required result for each real perfect-game sample:

```text
game_id
outs recorded
batters faced
hits
walks
other baserunner evidence
verdict
```

If perfection cannot be proved, downgrade/remove the achievement rather than guessing.

## Audit C — Special-record highest-only hierarchy

Current reported behavior:

```text
PERFECT_GAME
  > NO_HIT_NO_RUN
  > SHUTOUT_WIN
  > COMPLETE_GAME_WIN
```

and team equivalent.

The user's explicit highest-only examples were numeric families such as 5 hits suppressing 4 hits and 15 strikeouts suppressing 10 strikeouts. The implemented special hierarchy is a reasonable deduplication policy, but confirm and document that this is the project's canonical behavior:

- A perfect game persists only `PERFECT_GAME`, not duplicate no-hit/shutout/complete-game achievements.
- A no-hit-no-run persists only `NO_HIT_NO_RUN` within the special pitching family.
- Independent numeric achievements still coexist, e.g. `15 strikeouts + perfect game`.

Do not change this hierarchy unless a contradiction is found in the project requirement documents. Add/keep explicit tests so future work cannot accidentally reintroduce duplicates.

## Audit D — `STARTERS` vs `APPEARED` team batting semantics

Verify the exact participant set used by:

- `TEAM_STARTERS_ALL_HIT`
- `TEAM_APPEARED_ALL_HIT`
- `TEAM_STARTERS_ALL_RBI`
- `TEAM_APPEARED_ALL_RBI`

### Required interpretation audit

Document how these cases are handled:

- starting batter
- pinch hitter with PA/AB
- pinch hitter with PA but 0 AB (walk/sacrifice/etc.)
- pinch runner with no PA
- defensive replacement with no PA
- pitcher/non-hitter appearing only defensively, if applicable

The evaluator must not silently use a set whose baseball meaning is unclear.

Recommended default unless the existing implementation/report establishes a better source-backed definition:

- `STARTERS`: players in the starting batting lineup.
- `APPEARED`: players who actually participated offensively at the plate (at least one PA), not a pure pinch-runner/defensive appearance with no PA.

For an `ALL_HIT` achievement, every eligible participant must have at least one hit.
For an `ALL_RBI` achievement, every eligible participant must have at least one RBI.

If OOTP box data cannot distinguish PA reliably, document the closest safe rule and test it explicitly.

## Regression checks

After any fixes:

1. `compileall`
2. full pytest
3. full 7,682-game scan (or current full save count if changed)
4. zero parser failures expected unless source files changed/corrupted
5. repeated-game idempotency
6. highest-only threshold suppression
7. special hierarchy suppression
8. GUI smoke for corrected achievements

## Scope limits

Do NOT:

- implement season milestones
- implement career milestones
- build milestone rule editor UI
- add forecasts
- change unrelated GUI layout
- use roster exports
- modify/commit raw save files
- push or open PR

## Git policy

Local validation only. Prefer one local commit only if fixes/documentation changes are needed.

Suggested commit if fixes are required:

```text
fix: audit game milestone semantics
```

If no code changes are required, a documentation/test-only local commit is acceptable but not mandatory.

## Report format

```text
RESULT: PASS | FAIL

GRAND SLAM AUDIT
- positives sampled: <n>
- positive source parity: PASS/FAIL
- negatives sampled: <n>
- negative source parity: PASS/FAIL
- false positives found: <n>
- false negatives found: <n>

PERFECT GAME AUDIT
- real samples checked: <n>
- full no-baserunner proof: PASS/FAIL
- BF/outs or equivalent proof: PASS/FAIL

SPECIAL HIERARCHY
- pitcher highest-only: PASS/FAIL
- team highest-only: PASS/FAIL
- independent numeric coexistence: PASS/FAIL

TEAM PARTICIPANT SEMANTICS
- starters definition: PASS/FAIL
- appeared definition: PASS/FAIL
- pinch hitter handling: PASS/FAIL
- pinch runner / defensive-only handling: PASS/FAIL

REGRESSION
- compile: PASS/FAIL
- tests: PASS/FAIL
- full-save scan: PASS/FAIL
- parse failures: <n>
- idempotency: PASS/FAIL
- GUI smoke: PASS/FAIL

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
