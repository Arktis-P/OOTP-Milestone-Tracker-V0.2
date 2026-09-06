# Task 016B — Correct Real-Save Audit and Produce Actual Milestone Examples

## Goal

Correct the incomplete Task 016 audit and prove that the real application workflow produces correct records from the real OOTP save.

The previous Task 016 report is NOT sufficient for PASS because it reported:

```text
Games Scanned = 0
Game Milestone Achievements = 0
```

while still claiming Game / Season / Career / GUI PASS. It also reported only one stored `transaction_event` despite earlier Task 014 real-save results showing hundreds of parsed transactions. These discrepancies must be investigated and resolved.

This task has two equally important outputs:

1. a corrected end-to-end audit with hard failure gates;
2. an **actual-result example catalog** showing how each supported milestone/history family was really stored/rendered by the application from the current real save.

Repository: `Arktis-P/OOTP-Milestone-Tracker-V0.2`
Branch: `user/Workspace`
Primary save: `SuperYukies_V1.0.lg`

Before work:

```powershell
git fetch origin
git rebase origin/user/Workspace
```

Read first:

- `.agents/rules/workflow.md`
- `docs/REAL_SAVE_AUDIT_AND_RESET_DESIGN.md`
- `docs/ai/TASK_016_END_TO_END_REAL_SAVE_AUDIT.md`
- `docs/GAME_MILESTONE_CATALOG.md`
- `docs/SEASON_TRACKING_DESIGN.md`
- `docs/CAREER_AND_CONTEXT_DESIGN.md`
- `docs/HISTORY_MILESTONE_DESIGN.md`
- `docs/TRANSACTION_HISTORY_DESIGN.md`
- `docs/research/OOTP27_END_TO_END_APP_RESULT_AUDIT_LOCAL.md`

Do not re-research already confirmed source architecture unless a discrepancy forces it.

---

# 1. Correct the previous audit result first

The existing audit document currently claims PASS despite an empty Game Ledger rebuild. Treat that as an audit defect.

The corrected audit must not claim PASS when a required source family was not actually rebuilt and inspected.

Replace unsupported PASS statements with actual verified results.

Known issues requiring investigation:

```text
previous audit:
Games = 0
GameAch = 0
Imported game boxscores = 0

known prior full-save scan:
approximately 7,682 game_box files
parser failures = 0
```

and:

```text
Task 014 report:
trades parsed = 383
FA signings parsed = 243
extensions parsed = 16

Task 016 report:
transaction_events = 1
TRADE history rows = 65
```

Do not explain these by assumption. Measure each stage explicitly.

---

# 2. Hard discovery gates

Before deleting/rebuilding anything, run the application's canonical save scanner against the configured `.lg` root.

Use `scan_league_save()` / the same recursive source-discovery logic used by the product. Do not use an audit-only glob that searches the wrong directory level.

Record:

```text
save root
game_boxes discovered
logs discovered
messages discovered
player_stats discovered
```

Hard fail conditions:

- configured save root does not exist
- `game_boxes == 0`
- `messages == 0`
- discovered source counts differ drastically from prior known save inventory without a documented source-state change

For this known save, the worker should expect approximately:

```text
game_boxes ~= 7,682
messages = 10,098
```

Exact game count may differ only if the save itself changed. If so, document the new source count and evidence.

The audit script must explicitly abort instead of continuing with `Games=0`.

---

# 3. Product-flow rebuild

Use the same services/actions used by the application.

Required sequence:

```text
protect/backup current runtime DB
→ All Parsed Tracking Data Reset
→ confirm settings / tracked team / name mappings preserved
→ discover source files
→ import baseline/checkpoint if required
→ import ALL discovered game boxes (+ matching logs when available)
→ rebuild season aggregates
→ rebuild career aggregates/checkpoints
→ full history/message scan
→ finalize/reconcile completed regular seasons only where source data supports it
```

Do not populate milestone tables with hand-written audit SQL.

Diagnostic SQL is allowed only for inspection.

After game import, the following must be non-zero unless the source genuinely contains none:

```text
games
player_game_batting
player_game_pitching
game_milestone_achievements
```

Record parser failure count separately.

---

# 4. Transaction pipeline parity audit

Print counts at EVERY layer instead of only the final table count.

Required breakdown:

```text
transaction candidate messages
messages classified as TRADE
messages classified as FA_SIGNING
messages classified as CONTRACT_EXTENSION
raw parsed TransactionEventRecord count
stored transaction_events by transaction_type
stored transaction_participants by participant_kind
fan-out player_history_events by transaction subtype
tracked-team inbound player rows
tracked-team outbound player rows
unresolved transaction candidates
intentional exclusions
```

Then explain mathematically why counts differ.

Example of an acceptable explanation shape:

```text
383 parsed TRADE events
→ 383 transaction_events
→ 812 player participants
→ 812 player history fan-out rows
→ 65 rows visible under tracked-team filter
```

The actual numbers must come from the current save; do not use the example numbers above as expected output.

If `transaction_events=1` remains, treat as FAIL and fix the storage/replacement/audit logic before continuing.

---

# 5. Actual-result example catalog — mandatory

Create or replace a dedicated section in:

`docs/research/OOTP27_END_TO_END_APP_RESULT_AUDIT_LOCAL.md`

named:

`## Actual App Output Examples by Milestone Family`

This is not a template section. Fill it with **actual rows generated by this real save and current application code**.

Each example must contain:

```text
Family / Rule
Player or Team
Season / Date
Source ID (game_id or message_id)
Source file relative path
Actual DB title
Actual DB context_text
Actual UI-facing rendered text (if different)
Structured/evidence summary
Verdict: PASS / FAIL
```

Also include a brief source evidence summary proving the output, without dumping large raw source files.

If a supported family has no real occurrence in this save, write exactly:

`NO REAL SAMPLE IN CURRENT SAVE`

Then, if a deterministic fixture/test covers it, add a separate `Fixture-only example` subsection. Never present a fixture as a real-save example.

---

# 6. Required real examples — Game milestones

For threshold families, one actual example per family is mandatory; additionally show interesting/highest available thresholds when present.

## Batter game

- Hits (`GAME_HITS_*`)
- RBI (`GAME_RBI_*`)
- Multi-HR (`GAME_HR_*`)
- Grand slam
- Cycle
- Stolen bases (`GAME_SB_*`)

Preferred output shape:

```text
### Batter Game — Hits
- Actual player: <name>
- Game: <game_id>, <date>
- Rule: GAME_HITS_5
- DB title: <actual>
- DB context: 6타수 5안타
- Source evidence: box batting row AB=6, H=5
- Verdict: PASS
```

For multi-HR, grand slam and cycle, prove chronological/play context when the application claims it.

## Pitcher game

- Strikeouts (`GAME_STRIKEOUTS_*`)
- Complete-game win
- Shutout win
- No-hit no-run
- Perfect game

If no no-hitter/perfect game exists, mark no real sample and show fixture-only evidence separately.

## Team game

- starting lineup all hit
- all appearing batters hit
- starting lineup all RBI
- all appearing batters RBI
- team shutout
- team no-hit no-run
- team perfect game

For lineup rules, list the actual resolved lineup/player names from the stored context/evidence.

---

# 7. Required real examples — Season milestones

Use actual `season_milestone_achievements` created by the clean rebuild.

## Batter season counting

Show at least one actual row for each family when present:

- H
- HR
- RBI
- R
- SB
- BB

For each, show:

```text
pre-game cumulative value
achievement game delta
post-game cumulative value
threshold crossed
actual achievement game/date
actual rendered context
```

When an exact play is claimed, verify the log event.

## Batter season rate

- AVG
- OBP
- OPS

Show actual finalized/reconciled value and the selected tier. Confirm only the intended final tier is stored according to current rules.

## Pitcher season counting

- IP
- SO
- W
- HOLD
- SV

Show the same pre-game / game delta / post-game evidence.

## Pitcher season rate

- ERA
- FIP

FIP must remain `UNAVAILABLE` unless a new source was explicitly re-researched and proven. Do not fabricate a FIP example.

## Team season / postseason progression

Show real examples when present for:

- regular-season W threshold
- postseason berth
- division champion
- Wild Card Series win
- Division Series win
- League Championship Series win
- World Series win

Use actual tracked-team rows and actual record/series result text.

---

# 8. Required real examples — Career milestones

Use actual `career_milestone_achievements` from the clean rebuild.

## Batter career

- Games appeared
- Hits
- Home runs
- Runs
- RBI
- Stolen bases
- Walks

For post-baseline crossings, show:

```text
checkpoint value
post-checkpoint delta before game
game delta
resulting total
threshold
actual crossing game/context
```

For pre-baseline/checkpoint-import milestones, explicitly show that exact game context is absent and was not fabricated.

## Pitcher career

- Games appeared
- Games started
- Innings
- Strikeouts
- Wins
- Holds
- Saves

Apply the same checkpoint/delta evidence rules.

Also show at least one open-ended ladder example above the first threshold if the current save contains one.

---

# 9. Required real examples — History / non-stat milestones

Use actual `player_history_events`, `transaction_events`, `transaction_participants`, and `injury_episodes` produced by the current application.

## Injury

At minimum show:

- one simple diagnosis/duration milestone
- one injury with laterality/body-part when available
- one linked episode with occurrence → IL → return, when available

Example format must use the actual app text, e.g. whatever the DB currently rendered, not the specification's synthetic example.

Prove diagnosis and duration from the source message.

## All-Star

Show when available:

- fan-vote `*` / starter case
- manager/reserve case

Confirm minor-league All-Star and intermediate voting news are excluded.

## Awards

Show real examples for each available category:

- Platinum Stick / Silver Slugger
- Gold/Golden Glove
- MVP
- Cy Young
- Rookie of the Year
- Reliever award
- Player/Batter of Month
- Pitcher of Month
- Rookie of Month

For voted awards, verify actual vote count/unanimity wording when shown.

## Manual league-title UX

These are user-entered rather than message-derived.

Do not pollute the user's production DB merely to create examples.

Use a copied/audit DB or controlled temporary DB and exercise the **actual quick-add service/dialog path**.

Provide one actual app-generated example each for:

Batter:
- AVG
- H
- OBP
- HR
- RBI
- SB
- R
- OPS

Pitcher:
- W
- ERA
- IP
- SO
- SV
- HOLD
- WPCT

If finalized season data is unavailable for a category, report the limitation rather than inventing a value.

Clearly label these examples `CONTROLLED AUDIT DB — MANUAL INPUT`, not real-save automatic events.

## Transactions / contracts

Show real examples for:

- ordinary trade
- multi-player trade
- cash trade
- FA signing
- contract extension

For every trade example display:

```text
canonical transaction description
all participants grouped by side
from_team → to_team for every player
cash side + amount
all generated player-history fan-out rows
which rows are visible under tracked-team filter
```

If PURCHASE has no source sample, retain `NO REAL SAMPLE IN CURRENT SAVE`.

## Other career history

Show actual real-save examples when available for:

- Draft
- MLB debut
- Retirement
- Hall of Fame
- MLB call-up
- option/demotion/roster move
- position change if currently supported as history

If a category was intended but parser support is unresolved, mark FAIL/UNRESOLVED rather than silently omitting it.

---

# 10. Semantic verification rules

An example is PASS only if all source-proven semantic pieces are correct.

Do not accept only `player_id` + title matching.

Examples:

### Trade
Verify players, sides, old/new teams, cash side, cash amount, common description, fan-out identity.

### Injury
Verify injury name, duration, optional side/body part, event date, episode linkage.

### Season/career crossing
Verify actual cumulative boundary and exact crossing game; verify exact play only if rendered.

### All-Star
Verify MLB vs minor, starter/fan-vote marker, league/position where displayed.

### Award
Verify award subtype, league, position, vote count, unanimity where displayed.

### Team lineup milestone
Verify every listed starter/appeared player corresponds to the source game.

No fabricated detail is allowed to pass merely because it sounds plausible.

---

# 11. False-negative / false-positive matrix

For every supported event family include:

```text
source candidates
parsed candidates
published rows
unresolved rows
intentional exclusions
unexpected misses
unexpected positives
```

For transaction families also include transaction-event and participant counts separately.

For game milestone families compare eligible games against stored achievements where practical.

---

# 12. Determinism — corrected

Perform two full clean rebuilds only AFTER successful source discovery and non-zero game import.

Hard gate:

```text
if rebuild.games == 0:
    FAIL
```

Fingerprint both cycles using semantic stable fields for:

- games
- game achievements
- season achievements
- career achievements
- history events
- transaction events + participants
- injury episodes + episode events

A `0 == 0` comparison for a source family that should contain data is not a PASS.

---

# 13. GUI verification

Do not infer GUI PASS by reading UI source code.

Run the PySide6 application locally and inspect actual rendered rows after the clean rebuild.

At minimum verify one actual row from:

- Game Achievements
- Season Achievements
- Career Achievements
- History/Awards
- transaction display
- injury display
- player chronological history/timeline if exposed
- reset actions/result feedback

Screenshot capture is optional; the markdown report must at minimum record the displayed text exactly as observed.

Also verify whether reset controls are actually reachable through the user-facing Tools/Settings UI. If the service exists but the GUI action is absent, mark GUI reset workflow FAIL and fix it.

---

# 14. Defect repair rules

Audit defects are expected.

For every defect:

1. record failing source/result example;
2. identify root cause;
3. make minimal fix;
4. add regression test;
5. reset affected scope;
6. rerun affected real-save examples;
7. rerun full pytest + compileall at the end.

Local checkpoint commits only during work.

Do not push, open PRs or trigger remote CI unless the user explicitly requests it.

Suggested final local feature commit after all fixes/audit are complete:

`fix: complete real-save milestone result audit`

---

# 15. Required corrected report structure

Update:

`docs/research/OOTP27_END_TO_END_APP_RESULT_AUDIT_LOCAL.md`

It must contain these top-level sections:

```text
1. Audit Environment / Commit
2. Source Inventory
3. Clean Rebuild Counts
4. Transaction Pipeline Count Reconciliation
5. Actual App Output Examples by Milestone Family
   5.1 Game — Batter
   5.2 Game — Pitcher
   5.3 Game — Team
   5.4 Season — Batter
   5.5 Season — Pitcher
   5.6 Season — Team
   5.7 Career — Batter
   5.8 Career — Pitcher
   5.9 History — Injury
   5.10 History — All-Star
   5.11 History — Awards
   5.12 History — Manual League Titles
   5.13 History — Transactions / Contracts
   5.14 History — Other Career Events
6. Candidate-to-Result False Negative / Positive Audit
7. Determinism Rebuild Comparison
8. GUI Spot Audit
9. Defects Found and Fixes
10. Remaining Unsupported / No-Sample Families
11. Final Verdict
```

Every example table should use actual data columns similar to:

| Family | Rule/Subtype | Entity | Date | Source ID | Source Ref | Actual title/context | Evidence | Verdict |
|---|---|---|---|---|---|---|---|---|

Do not paste huge source bodies into the document.

---

# 16. Final report to user/top-level worker

Return a compact report plus several representative actual examples.

Required shape:

```text
RESULT: PASS | FAIL

SOURCE DISCOVERY
- game boxes: <n>
- logs: <n>
- messages: <n>
- player stat exports: <n>

CLEAN REBUILD
- games imported: <n>
- parser failures: <n>
- game achievements: <n>
- season achievements: <n>
- career achievements: <n>
- history events: <n>
- transactions: <n>
- injury episodes: <n>

TRANSACTION PARITY
- candidates: <n>
- parsed TRADE: <n>
- stored TRADE transaction_events: <n>
- FA: <n>
- extension: <n>
- participants: <n>
- fan-out history rows: <n>
- tracked IN rows: <n>
- tracked OUT rows: <n>

ACTUAL EXAMPLE COVERAGE
- game batter families: <covered>/<supported>
- game pitcher families: <covered>/<supported>
- game team families: <covered>/<supported>
- season batter families: <covered>/<supported>
- season pitcher families: <covered>/<supported>
- season team families: <covered>/<supported>
- career batter families: <covered>/<supported>
- career pitcher families: <covered>/<supported>
- history families: <covered>/<supported>
- no-real-sample families: <list>

REPRESENTATIVE ACTUAL OUTPUTS
- <Family>: `<actual app text>` — source <id/ref> — PASS/FAIL
- <Family>: `<actual app text>` — source <id/ref> — PASS/FAIL
- ... at least 12 representative outputs across game/season/career/history

FALSE RESULT AUDIT
- unexpected false positives: <n>
- unexpected false negatives: <n>
- unresolved documented: <n>

DETERMINISM
- rebuild 1 vs 2: PASS/FAIL

GUI
- actual row display: PASS/FAIL
- reset workflow reachable: PASS/FAIL

TESTS
- pytest: <n>/<n> PASS
- compileall: PASS/FAIL

AUDIT FILE
- docs/research/OOTP27_END_TO_END_APP_RESULT_AUDIT_LOCAL.md

FIXES
- <commits or NONE>

BLOCKERS / LIMITATIONS
- <items or NONE>
```

Do not return PASS unless the actual game import, season/career rebuild, real-source semantic examples, and corrected determinism gates all passed.
