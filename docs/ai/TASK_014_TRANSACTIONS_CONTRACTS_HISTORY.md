# Task 014 — Transactions & Contracts History Milestones

## Goal

Implement message-driven transaction/contract history milestones on top of the completed Task 013 message pipeline.

This task must use the already-prepared shared transaction model instead of creating a second unrelated history system.

Read first:

- `docs/TRANSACTION_HISTORY_DESIGN.md`
- `docs/research/OOTP27_PLAYER_HISTORY_SOURCE_RESEARCH_LOCAL.md`
- `docs/HISTORY_MILESTONE_DESIGN.md`
- `src/ootp_milestone_tracker/importer/message_source.py`
- `src/ootp_milestone_tracker/importer/message_models.py`
- `src/ootp_milestone_tracker/importer/transaction_models.py`
- `src/ootp_milestone_tracker/services/transaction_renderer.py`
- `src/ootp_milestone_tracker/services/transaction_service.py`
- `src/ootp_milestone_tracker/services/history_service.py`
- `.agents/rules/workflow.md`

Preserve Task 006–013 behavior. Do not redesign game/season/career milestones, awards, all-star, injury, or manual league-title workflows.

No PR, no GitHub Actions, no remote CI, no push from the local worker.

## Remote preparation already done

Do not redo these unless a local defect requires repair:

- transaction event/participant schema module
- transaction event/participant dataclasses
- canonical trade/contract renderer helpers
- atomic transaction persistence + per-player fan-out service
- transaction design document

Local work should concentrate on **real OOTP source parsing, integration, validation, and necessary fixes**.

---

# Phase 0 — Exact real-message pattern calibration

Do not perform another broad source-tree research pass. Task 012 already established candidate families and counts.

Instead, inspect representative actual `messages/message*.txt` samples specifically to establish exact grammar for:

### Trade

At minimum inspect samples across:

- one-for-one trade
- multi-player trade
- unequal player counts
- trade with cash if present
- messages with multiple team/player markup tags
- any trade wording variants such as `Trade`, `Deal`, `Dealt`, `Acquire`, `Confirm Deal`

Research already found about 1,481 trade samples; use enough varied real messages to prove parser rules rather than one title pattern.

### FA signing

Inspect actual body formats for:

- player
- signing team
- contract years
- total value
- date
- any messages missing years/value

Research found about 223 samples.

### Contract extension

Inspect all/most available variants because the sample count is small (~13).

### Purchase

Search real messages for deterministic player-purchase semantics (`purchase`, `purchased`, `contract purchased`, or equivalent).

- If real examples exist: document exact pattern and implement `PURCHASE`.
- If not: report `NOT AVAILABLE IN SAMPLE`; do not fabricate.

### Secondary transaction families

Inspect deterministic patterns for waiver/release/DFA/roster moves only as needed. The priority published milestones remain TRADE / FA_SIGNING / CONTRACT_EXTENSION / confirmed PURCHASE.

Update or append exact findings to:

`docs/research/OOTP27_PLAYER_HISTORY_SOURCE_RESEARCH_LOCAL.md`

Do not rewrite unrelated Task 012 research.

---

# Part A — Transaction parser

Implement:

`src/ootp_milestone_tracker/importer/transaction_parser.py`

Primary API:

```python
parse_transaction_message(msg: RawMessage) -> list[TransactionEventRecord]
```

Requirements:

1. conservative positive matching; unrelated message must return `[]`;
2. use explicit OOTP player/team IDs from markup;
3. preserve source player/asset order when deterministic;
4. preserve exact source/destination team semantics;
5. never infer a side merely from current `players.team_id`;
6. never infer cash amount, contract term, contract value, option years, or purchase semantics;
7. fill `event_key` deterministically within the source message;
8. exact source message identity/signature must survive into the transaction record.

If exact from/to semantics cannot be proven for an event, do not publish a false player movement. Keep it unresolved or skip it and report the pattern.

---

# Part B — Trade grouping and descriptions

A trade is one normalized `TransactionEventRecord` with N participants/assets.

Use participant fields:

```text
participant_kind
player_id
display_text
from_team_id
to_team_id
cash_amount
role
sequence
```

For a two-team trade, every player asset must have deterministic `from_team_id` and `to_team_id` where source allows it.

All involved players must receive their own `player_history_events` row after persistence.

All rows from the same trade use the same canonical description.

Required canonical example:

```text
애런 저지 & 게릿 콜 <> 오타니 쇼헤이 & 현금 $10,000,000 트레이드
```

Formatting rules are defined in `docs/TRANSACTION_HISTORY_DESIGN.md` and `transaction_renderer.py`.

### Cash

- exact value known -> `현금 $10,000,000`
- confirmed cash with no exact value -> `현금`
- no confirmed cash -> do not add it

### Multi-player fan-out

If tracked team A trades two players for one player from team B, all three player history rows must be created.

Tracked-only UI must show both:

- players leaving tracked team;
- player(s) arriving at tracked team.

This must work even after `players.team_id` reflects the player's later/current team.

---

# Part C — FA signing

Normalized subtype:

`FA_SIGNING`

Canonical description:

```text
12년 $333,333,000 FA 계약 체결
```

Graceful source-safe degradation is allowed:

```text
12년 FA 계약 체결
$333,333,000 FA 계약 체결
FA 계약 체결
```

Store:

- player ID
- destination/signing team ID
- event date/season
- years when explicit
- total value when explicit

Represent player movement as free agent/unknown source -> signing team. Do not invent a former team solely from current/historical roster state.

---

# Part D — Contract extension

Normalized subtype:

`CONTRACT_EXTENSION`

Canonical description:

```text
4년 $3,600,000 연장 계약 체결
```

The participant should normally preserve same-team semantics (`from_team_id == to_team_id`) when message proves the team.

### Options

Only render an option structure such as:

```text
10+2년
```

when the source explicitly provides the option years.

If the message only says 12 years, render `12년`.

Do not infer options from salary tables or contract totals in this task unless a separate authoritative source is explicitly proven and documented.

---

# Part E — Purchase

If Phase 0 confirms actual OOTP purchase semantics, implement normalized subtype:

`PURCHASE`

Use only source-proven fields and add a concise Korean description derived from the actual message semantics.

If no sample exists, implementation is not required and the final report must say:

`PURCHASE: NOT AVAILABLE IN SAMPLE`

---

# Part F — Integration with Task 013 message pipeline

Integrate `parse_transaction_message` into the existing historical/incremental message scan.

For each scanned source message:

1. run the transaction parser;
2. call `TransactionService.replace_source_transactions(...)` with the parser result for that source message when appropriate;
3. ensure changed-message rescans replace stale transaction participants and stale per-player history rows;
4. same message + same content must remain idempotent;
5. existing award/all-star/injury rows must not be duplicated or changed.

Do not make `messages.dat` a mandatory primary parser dependency. It remains optional metadata/index support.

---

# Part G — History UI

Existing target surface:

`Milestones > History / Awards`

Requirements:

- map `TRANSACTION` to a concise Korean type label such as `이적/계약`;
- existing search continues to match player name and description;
- tracked-only filtering proves event-time IN/OUT semantics;
- same trade description is visible on every involved player's row;
- no new top-level navigation item;
- no major visual redesign.

Do not implement the final unified career timeline redesign in this task.

---

# Part H — Secondary transaction events

Task 012 confirmed waiver/release/DFA/roster moves exist.

You may parse/store these in the shared transaction tables when deterministic, but the user has not finalized canonical display text for every subtype.

Therefore:

- do not block Task 014 PASS on publishing every secondary subtype;
- do not invent Korean descriptions just to claim support;
- report each as `CONFIRMED STORED`, `UNRESOLVED`, or `NOT IMPLEMENTED`;
- priority PASS scope is trade + FA signing + extension + purchase if available.

---

# Required tests

## Pure renderer tests

At minimum:

- two-player vs player+cash trade exact string;
- cash without amount;
- FA years+value;
- extension years+value;
- option omitted by default;
- explicit option rendered as `10+2년`.

## Controlled parser fixtures

Create sanitized/minimal fixtures representing real observed source structures for:

- 1-for-1 trade
- multi-player trade
- trade with cash when available
- FA full terms
- FA missing one optional term
- extension
- negative/non-transaction message
- purchase positive fixture only if real source confirms it

## Persistence/fan-out

Prove:

- one trade -> one transaction event;
- N player participants -> N history rows;
- all history rows share identical trade description;
- tracked outgoing player visible in tracked-only history;
- tracked incoming player visible in tracked-only history;
- unrelated-side/current-team changes do not break tracked filtering;
- same source repeated is idempotent;
- changed source removes stale old participant rows;
- changed source adds new participant rows correctly.

## Real-save audit

Use current `SuperYukies_V1.0.lg`:

- scan all transaction candidate messages;
- manually compare at least 30 diverse parsed trades against raw messages;
- compare at least 20 FA signings when samples allow;
- compare all or at least 10 extensions when samples allow;
- audit cash-containing trades if any;
- audit purchase candidates if any;
- report unresolved candidate counts by subtype.

## Regression

- `python -m compileall -q src scripts tests` PASS
- all pytest PASS
- Task 013 history non-transaction row counts/identities unchanged except intentional parser repairs
- full 7,682 game-box scan remains 0 parse failures
- no duplicate existing milestones

---

# Required report

```text
RESULT: PASS | FAIL

TRANSACTION PIPELINE
- historical backfill: PASS/FAIL
- incremental scan: PASS/FAIL
- changed-message replacement: PASS/FAIL
- idempotency: PASS/FAIL

TRADE
- exact side parsing: PASS/FAIL
- multi-player grouping: PASS/FAIL
- cash parsing: PASS/FAIL/NO SAMPLE
- one event / N player fan-out: PASS/FAIL
- common description: PASS/FAIL
- tracked IN/OUT semantics: PASS/FAIL

CONTRACTS
- FA signing: PASS/FAIL
- FA years/value: PASS/FAIL
- extension: PASS/FAIL
- extension years/value: PASS/FAIL
- option no-fabrication: PASS/FAIL

PURCHASE
- source status: CONFIRMED/NOT AVAILABLE
- parser: PASS/FAIL/NOT APPLICABLE

SECONDARY EVENTS
- waiver: CONFIRMED STORED/UNRESOLVED/NOT IMPLEMENTED
- release: CONFIRMED STORED/UNRESOLVED/NOT IMPLEMENTED
- DFA: CONFIRMED STORED/UNRESOLVED/NOT IMPLEMENTED
- roster move: CONFIRMED STORED/UNRESOLVED/NOT IMPLEMENTED

GUI
- transaction history type: PASS/FAIL
- search: PASS/FAIL
- tracked-only event-time filtering: PASS/FAIL

REAL SAVE AUDIT
- transaction candidate messages: <n>
- trades parsed: <n>
- FA signings parsed: <n>
- extensions parsed: <n>
- cash trades parsed: <n or NO SAMPLE>
- unresolved candidates: <n>
- source parity: PASS/FAIL

REGRESSION
- compile: PASS/FAIL
- tests: PASS/FAIL (<n>/<n>)
- game full-save scan: PASS/FAIL
- parser failures: <n>

FIXES
- NONE or list

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE or exact blockers
```

Suggested local commit:

`feat: add transaction and contract history milestones`

Do not push.
