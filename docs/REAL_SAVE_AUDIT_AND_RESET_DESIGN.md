# Real Save Audit & Reset Design

## Purpose

The application needs a repeatable way to prove that its actual product workflow produces correct milestone/history records from a real OOTP save.

Two separate concerns must remain distinct:

1. **Feature validation** — unit/fixture/full-save regression proving parsers and services work.
2. **Product result audit** — clear the runtime tracking DB, run the same import actions the user will use, and compare actual DB/UI output against source files.

Task 015 completes the product and reset tools. Task 016 performs the end-to-end result audit.

---

## Reset levels

### 1. History / Message Tracking Reset

Cheap reset for message-derived features.

Clear automatic message-derived history, transactions and injury episode state while preserving Game Ledger, season/career state, user settings and manual history by default.

This reset exists so history parser fixes can be tested repeatedly without rescanning thousands of game boxes.

### 2. All Parsed Tracking Data Reset

Clear all derived/imported tracking results needed for a clean product rebuild while preserving user configuration and source files.

The normal app workflow after this reset must be able to rebuild the same semantic DB state deterministically.

### 3. Factory/sample reset

Existing development/sample behavior. Keep it separate and clearly named so a user does not accidentally confuse it with OOTP tracking resets.

---

## Preservation rules

Default resets must never touch the OOTP `.lg` source folder.

Preserve whenever possible:

- configured save path
- tracked-team setting
- theme/UI settings
- user milestone thresholds
- Korean player-name mappings
- manual league-title records during history-only reset

If a technical dependency prevents preserving a field during all-tracking reset, document and fix the ownership model rather than silently discarding user data.

---

## Transactional reset

Every reset should:

1. calculate affected row counts
2. show confirmation
3. delete inside one SQLite transaction
4. rollback on error
5. refresh UI
6. report deleted/preserved counts

Repeated reset of an already-cleared scope must succeed safely.

Foreign-key deletion order must be explicit. Child tables such as transaction participants and injury episode events must be handled before/with parents unless cascade behavior is intentionally defined and tested.

---

## Deterministic rebuild identity

A clean rebuild is correct only when semantic records remain stable across repeated runs.

Autoincrement IDs and timestamps are not semantic identities. Audit fingerprints should instead use stable keys such as:

- `game_id + rule_key + entity/player_id`
- season achievement identity
- career achievement identity
- `source_family + source_event_id + player_id + event_subtype`
- transaction source/event key plus normalized participants
- injury occurrence source message plus normalized episode events

Normalized content should include the values users care about: dates, teams, thresholds, descriptions, participant sides and structured context.

---

## Product-flow rule

The final audit must not populate SQLite directly or call internal parser functions as the primary test path.

Use the same product actions/services exposed to the user:

```text
Reset
→ configure/confirm save
→ import/update games
→ import/reconcile stats when needed
→ scan history
→ inspect Milestones / Player Records / History
```

Direct SQL and parser helpers may be used only to inspect/diagnose results.

---

## Audit evidence model

For every sampled published record retain a reproducible chain:

```text
source_ref
source event/game id
expected normalized event
actual DB stable identity
actual rendered description
UI visibility/result
verdict
```

The audit report should explicitly record mismatches rather than summarizing only successful counts.

---

## False-positive and false-negative auditing

Successful output samples alone are insufficient.

For each event family compare source candidates against output classification:

```text
candidate
├─ published
├─ unresolved
├─ intentionally excluded
└─ unexpected miss
```

Also inspect published rows that do not correspond to a valid source event as unexpected positives.

Known examples of intentional exclusion include minor-league All-Star records and intermediate All-Star voting updates.

---

## Audit order

Recommended order for efficient repeated work:

1. History-only reset + message audit
2. Fix history defects
3. Repeat history reset/reparse until stable
4. All-tracking reset + full product rebuild
5. Game audit
6. Season audit
7. Career audit
8. Full-history audit on clean rebuilt DB
9. Repeat clean rebuild and compare fingerprints
10. GUI spot audit

This keeps expensive 7,000+ game rescans out of the iteration loop until message/history features are stable.

---

## PASS definition

A PASS is not:

- compile succeeded
- parser failures are zero
- row counts look plausible
- second run produces no duplicates

A PASS means actual source evidence was compared with actual generated DB/UI output across every supported milestone/history family, unexpected misses/positives were investigated, and a clean reset/rebuild produced the same semantic result twice.