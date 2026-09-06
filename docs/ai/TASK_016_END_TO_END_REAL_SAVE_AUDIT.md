# Task 016 — End-to-End Real Save Result Audit

## Goal

After Task 015 is complete, verify the application as a product by repeatedly resetting its tracking DB, running the normal OOTP import/parsing workflow, and comparing the resulting milestone/history records against the actual source files from the real save.

This task answers the user's real question:

> When the actual app parses the save and inserts milestone/history records, are the records that appear in the DB and UI actually correct?

This is not a parser-unit-test task. Use the **same application actions/services that the user will use**. Diagnostic scripts may assist investigation but must not substitute for the product flow.

Repository: `Arktis-P/OOTP-Milestone-Tracker-V0.2`
Branch: `user/Workspace`

Read first:

- `.agents/rules/workflow.md`
- `docs/REAL_SAVE_AUDIT_AND_RESET_DESIGN.md`
- `docs/ai/TASK_015_COMPLETE_CAREER_HISTORY_AND_RESET_TOOLS.md`
- all existing local source-research documents under `docs/research/`

Primary real-save target currently used by research:

`SuperYukies_V1.0.lg`

Resolve the user's actual configured save path through the application; do not hard-code the Windows username/path.

---

# Audit principle

A PASS requires more than "parser failures = 0" or "counts are stable".

For each sampled record, prove:

```text
source file/message/game
    ↓
parsed normalized evidence
    ↓
DB identity/value/context
    ↓
UI description
```

and compare expected vs actual.

The audit must detect:

- false positives
- false negatives
- wrong player/team association
- wrong date/season
- wrong trade side
- duplicated achievements
- missed threshold crossings
- fabricated context
- stale records surviving reset/reparse
- incorrect Korean description rendering

---

# Stage 0 — Protect current runtime state

Before destructive tests:

1. Record current runtime DB path.
2. Make a local audit backup/copy outside the active DB path when practical.
3. Record current configured save path, tracked team, rule settings and key app settings.
4. Never modify any file inside the `.lg` save.

Audit backups/artifacts should remain local and ignored from Git unless they are small text reports intentionally added under `docs/research/`.

---

# Stage 1 — History/message clean rebuild

Use the product's **History / Message Tracking Reset** action.

Confirm:

- automatic history rows are cleared
- transaction rows are cleared
- injury episode rows are cleared
- manual history rows remain unless explicitly selected for deletion
- game/season/career ledger remains intact
- settings/mappings remain intact

Then trigger the application's **full history scan**.

Record exact counts by event type/subtype:

- injury occurrence
- All-Star starter/fan-vote and reserve/manager selection
- position awards
- MVP/Cy Young/ROTY/reliever award
- monthly awards
- manual titles (preserved, not regenerated)
- trade
- FA signing
- contract extension
- waiver/release/DFA if implemented
- MLB debut
- draft
- retirement
- Hall of Fame
- MLB call-up/option/demotion
- unresolved candidates

Run full history scan a second time without reset. There must be no duplicate event identities.

---

# Stage 2 — History source-to-result audit

Build a deterministic sample from actual produced DB rows. Prefer samples spread across seasons and source patterns rather than only the first rows.

Minimum audit targets when enough samples exist:

- Injury: 20 occurrences + all available linked IL/return/setback examples up to 20 each
- All-Star: 20 including fan-vote `*` and non-star selections
- Major awards: 20
- Position awards: 20
- Monthly awards: 20
- Trades: 30, including at least 10 multi-player and every available cash-trade sample up to 20
- FA signings: 20
- Extensions: all if <=20, otherwise 20
- MLB debut: all if sample count is small
- Draft: 15
- Retirement: all available if <=20
- Hall of Fame: all available if <=20
- MLB roster moves: 20

For every sampled automatic row:

1. Open/read its `source_ref`.
2. Verify player ID and displayed player name.
3. Verify team association/event-time tracked-team semantics.
4. Verify date and season.
5. Verify subtype.
6. Verify rendered title against the source.
7. Verify structured context contains only source-proven facts.
8. Verify no duplicate canonical event exists.

For trades additionally verify:

- every player is on the correct side
- `from_team_id` / `to_team_id` are correct
- cash is assigned to the correct side
- every relevant player has the same canonical common description
- tracked-team inbound and outbound players are all surfaced

For injuries additionally verify episode linkage across occurrence → IL/setback → return when samples exist.

---

# Stage 3 — Candidate-to-result false-negative audit

Do not audit only rows that the parser successfully produced.

Use source candidate searches/pattern inventories from Tasks 012–015 and compare candidate messages against:

- published DB event
- unresolved candidate
- intentionally excluded source
- parser miss

For every major event family, calculate/report:

```text
candidate source count
published count
unresolved count
intentional exclusions
unexpected misses
unexpected positives
```

Manually inspect all unexpected misses for small families (retirement/HOF/debut/extensions). For large families, inspect every miss if feasible or at minimum a meaningful capped sample and report the remaining count.

A known unsupported source pattern may remain unresolved only if documented precisely.

---

# Stage 4 — Clean all-tracking rebuild

Use the product's **All Parsed Tracking Data Reset** action.

Verify preserved configuration and absence of stale derived records.

Then use the application's normal user-facing workflow to rebuild from the actual save:

1. baseline/checkpoint import as required by the app
2. Update Games / Game Ledger scan
3. season aggregation
4. career aggregation/checkpoint state
5. history full scan
6. any regular-season finalization/reconciliation that is appropriate for completed seasons and supported by available exports

Do not directly populate tables with test SQL.

Record exact post-import counts for every major table/family.

---

# Stage 5 — Game milestone actual-result audit

From the freshly rebuilt DB compare actual milestone rows against the game box/log source.

Minimum targets when available:

### Batter game
- H family: 20
- RBI family: 20
- multi-HR: 15
- grand slam: 15
- SB: 15
- cycles: all available

### Pitcher game
- SO family: 20
- CG win: all/15
- shutout win: all/15
- no-hitter: all
- perfect game: all

### Team game
- all-hit starter/appeared: 10 each when available
- all-RBI: 10 each when available
- team shutout/no-hitter/perfect: all or representative samples

For each row verify the canonical threshold/hierarchy semantics and the displayed context against original box/log.

---

# Stage 6 — Season actual-result audit

Audit actual season milestone rows against:

- Game Ledger cumulative totals for exact crossing games
- finalized player stats export for reconciled/final rate values

Minimum sample targets:

### Batter
- H/HR/RBI/R/SB/BB: at least 10 per family when available
- AVG/OBP/OPS final tiers: 10 total or all available

### Pitcher
- IP/SO/W/HOLD/SV: at least 10 per family when available
- ERA final buckets: all/10
- FIP remains unavailable unless source rules have changed and were explicitly re-researched

### Team
- W thresholds: all available
- postseason berth/division/WCS/DS/LCS/WS: all available for the tracked team/save history

Verify exact crossing play when one is claimed; otherwise confirm fallback status does not fabricate details.

---

# Stage 7 — Career actual-result audit

Audit career totals and milestone crossings against:

```text
latest official career checkpoint
+ post-checkpoint regular-season game deltas
```

Minimum sample targets:

### Batter
- H/HR/R/RBI/SB/BB/G: 10 each when available

### Pitcher
- IP/SO/W/HOLD/SV/G/GS: 10 each when available

Verify:

- checkpoint cutoff prevents double counting
- postseason is not merged into regular-season career totals
- exact post-baseline crossing game is correct
- historical/pre-baseline thresholds do not fabricate exact game context
- open-ended ladders remain correct

---

# Stage 8 — Reset/rebuild determinism

This is mandatory.

Perform at least two clean rebuild cycles using the same real save:

```text
Reset all parsed tracking data
→ normal app import
→ capture normalized result fingerprints/counts
→ reset again
→ normal app import again
→ compare
```

Normalized fingerprints should ignore DB autoincrement IDs/timestamps that are not semantic identities.

Compare stable identities and content for:

- games
- game achievements
- season achievements
- career achievements
- automatic history events
- transaction events + participants
- injury episodes/events

Any semantic difference between rebuilds is a FAIL until explained/fixed.

Also verify incremental scans immediately after a complete scan do not add duplicates.

---

# Stage 9 — UI spot audit

Use the running PySide6 app and verify that audited records appear correctly in their actual user-facing surfaces.

At minimum inspect:

- Game Achievements
- Season Achievements
- Career Achievements
- History/Career History
- one player's chronological history
- transaction common descriptions
- injury episode details
- reset confirmation/result summaries

Do not claim GUI PASS from DB queries alone.

---

# Defect handling

If the audit finds defects:

1. record an example source ref and actual DB/UI output
2. identify root cause
3. fix only the necessary code
4. add regression fixture/test
5. reset relevant tracking scope
6. rerun the affected real-save audit slice
7. rerun full regression before PASS

Checkpoint fixes with local commits. Do not push/PR/remote-CI unless explicitly requested by the user.

---

# Required audit artifact

Create/update:

`docs/research/OOTP27_END_TO_END_APP_RESULT_AUDIT_LOCAL.md`

It must include:

- save identity/path sanitized as appropriate
- audit date
- exact code commit
- reset/rebuild procedure
- post-build DB counts
- per-family candidate/published/unresolved/miss counts
- sampled source-to-result comparisons
- all discovered mismatches and fixes
- repeat-build fingerprint comparison
- remaining source limitations

Use tables with source message/game IDs so another worker can reproduce checks.

---

# Required final report

```text
RESULT: PASS | FAIL

CLEAN REBUILD
- history reset/reparse: PASS/FAIL
- all tracking reset/reparse: PASS/FAIL
- settings/mappings preserved: PASS/FAIL

HISTORY RESULT AUDIT
- injuries: PASS/FAIL (<checked>/<mismatches>)
- All-Star: PASS/FAIL
- awards: PASS/FAIL
- transactions/contracts: PASS/FAIL
- debut/draft/retirement/HOF: PASS/FAIL
- roster moves: PASS/FAIL
- false-negative audit: PASS/FAIL

GAME RESULT AUDIT
- batter: PASS/FAIL
- pitcher: PASS/FAIL
- team: PASS/FAIL

SEASON RESULT AUDIT
- counting: PASS/FAIL
- rate/finalization: PASS/FAIL
- team progression: PASS/FAIL

CAREER RESULT AUDIT
- batter: PASS/FAIL
- pitcher: PASS/FAIL
- checkpoint/delta correctness: PASS/FAIL

DETERMINISM
- clean rebuild fingerprints: PASS/FAIL
- repeated full scan idempotency: PASS/FAIL
- incremental scan idempotency: PASS/FAIL

GUI
- audited rows displayed correctly: PASS/FAIL
- reset workflow: PASS/FAIL

REAL SAVE
- game boxes scanned: <n>
- messages scanned: <n>
- parser failures: <n>
- unexpected false positives: <n>
- unexpected false negatives: <n>

AUDIT FILE
- docs/research/OOTP27_END_TO_END_APP_RESULT_AUDIT_LOCAL.md

FIXES
- NONE or list commits

BLOCKERS / REMAINING SOURCE LIMITATIONS
- NONE or exact items
```

PASS means the worker has inspected actual generated records against actual source evidence, not merely that automated tests passed.