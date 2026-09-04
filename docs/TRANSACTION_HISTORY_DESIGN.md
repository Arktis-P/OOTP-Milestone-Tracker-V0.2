# Transaction & Contract History Design

## Scope

This document defines canonical transaction/history behavior for OOTP message-driven events after Task 013.

Primary goal:

> One real-world transaction event is stored once, while every involved player receives an individual history/milestone row that points to the same rendered description.

Task 014 covers message-driven transactions and contracts. It must preserve all Task 013 award/all-star/injury behavior.

## Canonical model

Use two levels:

```text
transaction_events          one row per real transaction event
  ↓
transaction_participants    N assets/players involved in that event
  ↓
player_history_events       one row per involved player
```

Do not duplicate the underlying trade just because four players are involved.

A multi-player trade such as:

```text
Aaron Judge + Gerrit Cole  ↔  Shohei Ohtani + cash $10,000,000
```

is one `transaction_events` row, participant rows for each player/cash asset, then separate `player_history_events` rows for Judge, Cole, and Ohtani with the same transaction description.

## Event-time team semantics

Never use a player's current team to decide whether an old transaction belongs to the tracked team.

Each player participant should preserve:

```text
from_team_id
to_team_id
```

For tracked-only history filtering:

1. if `from_team_id` is the tracked team, use it as the history row's event team;
2. else if `to_team_id` is the tracked team, use it;
3. otherwise use destination team when known, else source team.

Therefore both players leaving the tracked team and players arriving at the tracked team remain visible in tracked-only history even after their current roster membership changes.

## Trade participant model

Participant kinds are intentionally open:

- `PLAYER`
- `CASH`
- `DRAFT_PICK`
- `OTHER`

Only publish types actually proven by OOTP source data. Do not invent draft-pick or other assets just because the schema permits them.

For players, preserve player ID and source/destination team IDs.
For cash, preserve exact amount only when the message states it.
For any non-player asset, preserve the literal proven asset text.

## Trade description

The canonical display form is a single common description shared by all involved player history rows:

```text
애런 저지 & 게릿 콜 <> 오타니 쇼헤이 & 현금 $10,000,000 트레이드
```

Rules:

- preserve each side's source order when it is deterministic;
- join assets within one side using ` & `;
- separate the two sides using ` <> `;
- end with ` 트레이드`;
- use `현금 $10,000,000` when exact amount is available;
- use only `현금` when a cash component is confirmed but exact amount is not;
- never guess a cash amount;
- all player history rows generated from the same trade use this identical description.

The transaction database may also store team names/IDs, but the concise canonical history description does not require team names.

## FA contract description

Canonical form:

```text
12년 $333,333,000 FA 계약 체결
```

Extract only data explicitly present in the source message:

- player ID
- signing team ID
- contract years
- total contract value
- event date/season

Degraded but valid forms when message fields are absent:

```text
12년 FA 계약 체결
$333,333,000 FA 계약 체결
FA 계약 체결
```

Never manufacture missing terms.

## Contract extension description

Canonical form:

```text
4년 $3,600,000 연장 계약 체결
```

Use the same no-fabrication rules as FA contracts.

## Contract options

Preferred display if and only if the message explicitly proves an option structure:

```text
10+2년 $... 계약 체결
```

Do not infer options from total years, salary schedules, current contract state, or other files unless Task 014 proves an authoritative deterministic source.

If message data only says 12 years, render `12년`, not `10+2년`.

## Purchase / player purchase

The user wants player-purchase transactions supported if OOTP actually provides a deterministic message/source representation.

Task 014 must inspect real save samples for `purchase`, `purchased`, `contract purchased`, or equivalent semantics.

- If confirmed, add normalized subtype `PURCHASE` and document exact source pattern + description rule.
- If not present in the current sample, report `NOT AVAILABLE IN SAMPLE` and do not invent support.

## Waiver / release / DFA / roster moves

Task 012 confirmed these exist in messages. They may use the same structured transaction pipeline.

However the priority published milestone/history types for Task 014 are:

1. `TRADE`
2. `FA_SIGNING`
3. `CONTRACT_EXTENSION`
4. `PURCHASE` only if source-confirmed

Waiver, release, DFA, option/recalled moves may be parsed and stored when deterministic, but do not invent new Korean canonical descriptions where requirements are not yet fixed. If necessary, preserve them as structured/unresolved candidates and report coverage separately.

## Historical and incremental behavior

Task 013 message pipeline semantics remain mandatory:

```text
first connection
  -> historical message backfill

later refresh
  -> new messages only when possible

same source ID + same signature
  -> no duplicate

same source ID + changed signature
  -> replace transaction group and per-player history fan-out
```

Changed-message replacement must remove stale participants/history rows that are no longer present in the corrected source.

## Idempotency identity

Transaction event identity:

```text
(source_family, source_event_id, event_key)
```

Player history identity continues to use the existing history model:

```text
(source_family, source_event_id, player_id, event_subtype)
```

A single message containing different transaction subtypes may produce more than one normalized transaction event when source semantics prove they are distinct.

## Existing remote preparation

Task 014 preparation already provides:

- `db/transaction_schema.py`
- `importer/transaction_models.py`
- `services/transaction_renderer.py`
- `services/transaction_service.py`

`TransactionService.replace_source_transactions(...)` is designed so the local parser can replace all transaction rows generated by one source message atomically and fan out player history rows.

## UI

The existing `History / Awards` tab remains the target surface for this task.

Add `TRANSACTION` display mapping such as `이적/계약` without creating a new top-level navigation item.

Tracked-only filtering must be verified for both:

- tracked-team player leaving;
- outside player arriving at tracked team.

The same trade description should appear for every participant row generated from that trade.
