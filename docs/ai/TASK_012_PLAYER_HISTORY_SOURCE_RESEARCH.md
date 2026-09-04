# Task 012 — Player History Source Research

## Goal

Research which automatically available OOTP 27 save files can reliably support player/team history tracking after the completed game/season/career milestone pipeline.

This task is **research-first**. Do not build production award/injury/transaction/history UI yet unless a tiny parser prototype is necessary to prove source semantics. The output should establish which event families are safe to implement next, what source owns them, what IDs/dates can be trusted, and how incremental/idempotent detection should work.

Repository: `Arktis-P/OOTP-Milestone-Tracker-V0.2`
Branch: `user/Workspace`

Read first:

- `.agents/rules/workflow.md`
- `docs/ARCHITECTURE.md`
- `docs/OOTP_DATA_IMPORT_PLAN.md`
- `docs/research/OOTP27_SOURCE_INVENTORY_LOCAL.md`
- `docs/research/OOTP27_SEASON_STATS_RESEARCH_LOCAL.md`
- `docs/CAREER_AND_CONTEXT_DESIGN.md`

Preserve all completed game/season/career behavior. No PR, no GitHub Actions, no remote CI, no push from the local worker.

## Core principle

Do not assume `messages/message*.txt` is automatically the best source just because it already contains structured entity markup. Inspect the actual save tree and compare all automatically generated candidate sources.

`*_rosters.txt` must not become a routine dependency because it requires a manual export. It may be inspected only as optional corroboration if already present.

The production design should prefer sources that are:

1. generated automatically by OOTP;
2. stable across saves/seasons;
3. keyed by stable `player_id` / `team_id` where possible;
4. date/season resolvable;
5. incrementally detectable without rescanning/recreating history incorrectly;
6. deduplicable/idempotent;
7. capable of historical backfill when the source actually contains older events.

## Phase 1 — Save-tree inventory expansion

Inspect the real local save (`SuperYukies_V1.0.lg`) beyond the currently registered source families.

Inventory candidate files/directories that may contain:

- player history / biography / HTML player pages
- team history
- league history / standings / awards pages
- transaction logs
- injury logs
- news / messages
- contract/signing records
- retirement / Hall of Fame records
- roster/status snapshots that are generated automatically

For each candidate family record:

```text
relative path / pattern
file count
encoding / format
whether automatically generated
stable IDs present
explicit date/season present
historical vs current-state semantics
incremental identity candidate
```

Update/create:

`docs/research/OOTP27_PLAYER_HISTORY_SOURCE_RESEARCH_LOCAL.md`

Do not commit raw personal/save data or large raw samples. Sanitized tiny fixtures are allowed only if useful.

## Phase 2 — Awards research

Research at least the following event classes when present in the save:

- MVP / Most Valuable Player
- Cy Young / Pitcher award equivalents
- Rookie of the Year
- Gold Glove
- Silver Slugger
- All-Star selection
- Player/Pitcher of the Month or similar monthly awards
- custom league awards / other named awards OOTP exposes

For each award source verify:

- `player_id`
- award display name
- canonical/normalized award type if safely derivable
- season/year
- award date or announcement date when available
- league/subleague ID when available
- team ID at award time when available
- whether one award can generate multiple messages/files
- whether historical awards from previous seasons remain available
- whether a single source gives the authoritative history or only notifications

Do not hard-map arbitrary custom award names into MLB award types. Preserve raw OOTP award name and add a normalized type only for patterns proven by the sample/source.

## Phase 3 — Transactions / contracts research

Research distinct event types, not one generic "team changed" event.

At minimum inspect whether the save can reliably identify:

- trade
- free-agent signing
- contract extension
- release
- waiver claim
- waiver placement if useful
- purchase / transfer between organizations if represented
- minor-league signing if represented
- team change without explicit transaction type

For each candidate event verify:

- `player_id`
- event date
- old team ID
- new team ID
- transaction type
- contract terms if present (years/value/options) — only if source is clear
- other players involved in multi-player trades
- transaction counterpart teams
- event/message ID suitable for idempotency
- whether duplicate notifications exist for the same transaction

For trades, prefer preserving one transaction/event identity with related participants rather than inventing unrelated individual events when the source can prove they belong to the same trade.

## Phase 4 — Injuries research

Research whether the save can reliably reconstruct injury episodes rather than only current injury state.

Inspect support for:

- injury occurrence date
- injury name/type
- body part if separately represented
- severity / expected duration
- day-to-day vs injured list status
- IL placement
- injury extension/setback
- activation/return
- season-ending or career-ending wording when explicitly stated

Determine whether start and return events can be linked into one `injury_episode_id` or equivalent deterministic key.

Do not infer recovery dates solely from the disappearance of a player from an injury list unless the source semantics are proven reliable.

## Phase 5 — Other career-history events

Research, but do not force implementation, for:

- MLB/major-league debut if available
- call-up / option / demotion
- DFA
- retirement
- unretirement if represented
- Hall of Fame induction
- jersey retirement
- team captain/leadership events if explicitly recorded
- major league / organization debut if distinct

Retirement is especially important to classify, but **do not reintroduce retirement-rate milestones**. The app currently intentionally does not track final retired AVG/ERA/etc. This research is only about the retirement event itself and whether it can be stored in a career timeline.

## Phase 6 — Source authority matrix

Produce a source-authority matrix. Each event family must be classified as one of:

- `CONFIRMED_PRIMARY` — source directly and reliably contains the event
- `CONFIRMED_SECONDARY` — useful corroboration but not preferred authority
- `CURRENT_STATE_ONLY` — describes state but cannot reconstruct event history safely
- `AMBIGUOUS` — insufficient semantics
- `NOT_AVAILABLE_IN_SAMPLE`
- `UNSUPPORTED`

Required matrix columns:

```text
EVENT FAMILY
PRIMARY SOURCE
SECONDARY SOURCE
PLAYER ID
TEAM ID(S)
DATE
SEASON
HISTORICAL BACKFILL
INCREMENTAL DETECTION
IDEMPOTENT KEY
CONFIDENCE
NOTES
```

## Phase 7 — Incremental/idempotent model recommendation

For every event family judged implementable, recommend a canonical normalized event model.

Suggested generic shape:

```text
history_event_id
source_family
source_event_id / source_signature
entity_type
player_id nullable
team_id nullable
other_team_id nullable
event_type
event_subtype nullable
event_date nullable
season nullable
league_id nullable
title
context_text nullable
raw_source_ref
source_hash
```

Use family-specific child tables only when needed (for example injury episodes or multi-player trades).

Required behavior:

```text
new source event -> insert normalized history event
same source identity + same hash -> skip
same source identity + changed hash -> update/rebuild affected event
```

If source files are mutable/current-state snapshots rather than immutable events, document a different safe strategy instead of pretending the above identity works.

## Phase 8 — Historical backfill behavior

Determine what happens on first app setup when the OOTP save already contains years of history.

For each family answer:

- Can the app import historical events immediately?
- How far back does the actual source retain data?
- Are old message files retained indefinitely in the sample?
- Are there missing gaps?
- Can chronological ordering be trusted?
- Can the same event appear in both historical pages and messages?

Recommend whether first-run import should be:

- full historical backfill;
- recent-only backfill;
- current-state snapshot only;
- unsupported until new events occur.

## Phase 9 — Prototype parsing

Only when useful to prove semantics, create small research/prototype parsers under `scratch/` or similarly disposable location.

Do not wire them into production DB/UI in this task.

At minimum, if `messages/message*.txt` is confirmed useful, prove parsing of:

- message/source ID
- player IDs from `<Name:player#ID>`
- team IDs from `<Name:team#ID>`
- event date if present/derivable
- a few representative award, transaction, and injury patterns

Avoid giant regex tables without source evidence. Prefer a small set of proven examples and report unsupported variants.

## Validation / sample requirements

Use the real local save.

Where real positives exist, inspect multiple samples from different seasons/teams/players.

Target minimums when available:

- awards: 20 positive samples across multiple award types
- transactions/contracts: 30 positive samples across at least 3 event types
- injuries: 30 positive samples including start + return/activation when possible
- retirement/HOF/other: all available positives if sample count is small

Check representative negatives for any text classifier to estimate false positives.

Do not mark an event type PASS based only on one regex fixture when no actual source example was verified.

## No-production-implementation rule

This task should end with evidence and a recommended implementation order.

Do **not** implement the full history database, timeline UI, award tracker, injury tracker, or transaction tracker yet.

Small fixes are allowed only when needed to make research scripts run and must not change existing milestone semantics.

## Required output document

Create/update:

`docs/research/OOTP27_PLAYER_HISTORY_SOURCE_RESEARCH_LOCAL.md`

It must contain:

1. expanded source inventory;
2. award source mapping;
3. transaction/contract source mapping;
4. injury source mapping;
5. other career event mapping;
6. source authority matrix;
7. dedup/idempotency recommendations;
8. historical backfill recommendations;
9. exact known limitations;
10. recommended implementation sequence for Task 013+.

## Required report

```text
RESULT: PASS | FAIL

SOURCE INVENTORY
- expanded automatic source scan: PASS/FAIL
- new candidate families found: <list or NONE>

AWARDS
- authoritative source: <source / NONE>
- player_id: PASS/FAIL
- season/date: PASS/FAIL/PARTIAL
- historical backfill: PASS/FAIL/PARTIAL
- incremental detection: PASS/FAIL/PARTIAL
- sample types: <summary>

TRANSACTIONS
- trade: PASS/FAIL/NO SAMPLE
- FA signing: PASS/FAIL/NO SAMPLE
- extension: PASS/FAIL/NO SAMPLE
- release/waiver: PASS/FAIL/NO SAMPLE
- old/new team IDs: PASS/FAIL/PARTIAL
- multi-player trade grouping: PASS/FAIL/PARTIAL/NO SAMPLE

INJURIES
- occurrence: PASS/FAIL/NO SAMPLE
- injury type: PASS/FAIL/PARTIAL
- duration/severity: PASS/FAIL/PARTIAL
- IL placement: PASS/FAIL/NO SAMPLE
- return/activation: PASS/FAIL/NO SAMPLE
- episode linkage: PASS/FAIL/PARTIAL

OTHER HISTORY
- call-up/demotion: PASS/FAIL/NO SAMPLE
- retirement: PASS/FAIL/NO SAMPLE
- Hall of Fame: PASS/FAIL/NO SAMPLE
- other confirmed events: <list or NONE>

SOURCE AUTHORITY
- matrix completed: PASS/FAIL
- safe idempotent identities: PASS/FAIL/PARTIAL
- historical backfill strategy: PASS/FAIL

REGRESSION
- compile: PASS/FAIL
- existing tests: PASS/FAIL
- milestone full-save scan unchanged: PASS/FAIL

FILES
- docs/research/OOTP27_PLAYER_HISTORY_SOURCE_RESEARCH_LOCAL.md

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE or exact blockers

RECOMMENDED NEXT IMPLEMENTATION
1. <family>
2. <family>
3. <family>
```

Suggested local commit:

`research: map OOTP player history event sources`
