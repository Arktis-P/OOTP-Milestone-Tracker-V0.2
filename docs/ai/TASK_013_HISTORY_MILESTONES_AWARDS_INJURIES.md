# Task 013 — History Milestones: Awards, All-Star, Injuries, Manual League Leaders

## Goal

Implement the first production player-history milestone pipeline using the confirmed OOTP message sources from Task 012.

This task must implement:
1. common message-backed history-event infrastructure;
2. injury occurrence milestones;
3. MLB All-Star milestones;
4. automatic award milestones;
5. monthly award milestones;
6. fast manual entry for league-leading/stat-title awards;
7. Milestones-page UI integration.

Do NOT implement transactions/contracts in this task. Trades, FA signings, purchases, waiver/release, and extensions are the next task.

Read first:
- `.agents/rules/workflow.md`
- `docs/HISTORY_MILESTONE_DESIGN.md`
- `docs/research/OOTP27_PLAYER_HISTORY_SOURCE_RESEARCH_LOCAL.md`
- `docs/CAREER_AND_CONTEXT_DESIGN.md`
- `docs/ARCHITECTURE.md`

Preserve all Task 006–012 behavior and regression tests.

Repository: `Arktis-P/OOTP-Milestone-Tracker-V0.2`
Branch: `user/Workspace`

Local worker must not push. Use local commits only and report results.

---

# Phase 0 — Source-semantic verification before parser implementation

Use the local `SuperYukies_V1.0.lg` save to verify exact raw examples for each parser family before coding pattern logic.

Required verification samples:

### All-Star
- final MLB All-Star roster message(s)
- at least one player marked with `*`
- at least one non-`*` final selection
- at least one minor-league All-Star message
- at least one fan-voting update that must NOT produce a milestone

Prove:
- whether `*` exactly means fan-vote first-place/starter selection in the final roster representation;
- how AL/NL is represented;
- how position is represented;
- how MLB vs minor-league All-Star can be deterministically separated.

If `*` semantics cannot be proven, do not implement the special fan-vote wording yet; report it as unsupported instead of guessing.

### Awards
Find raw samples for:
- MVP
- Cy Young
- Rookie of the Year
- reliever award if available
- Platinum Stick / Silver Slugger equivalent
- Gold Glove / Golden Glove equivalent
- monthly batter/player award
- monthly pitcher award
- monthly rookie award

For major voted awards verify:
- vote-count wording;
- explicit or deterministic unanimity evidence;
- league/subleague identity.

### Injuries
Find raw samples for:
- one-sided body-part injury if available;
- injury with exact single duration;
- duration range;
- month-scale duration;
- day-scale duration;
- IL/activation messages associated with an occurrence.

Document any newly discovered source semantics by updating:

`docs/research/OOTP27_PLAYER_HISTORY_SOURCE_RESEARCH_LOCAL.md`

Do not broaden into transaction research; Task 012 already established those sources.

---

# Part A — Canonical history-event persistence

Add a durable DB model for message/manual history events. Use the design doc as the semantic source of truth.

Recommended table:

```sql
player_history_events
- id INTEGER PK
- source_family TEXT NOT NULL
- source_event_id TEXT NOT NULL
- source_signature TEXT NOT NULL
- source_mode TEXT NOT NULL
- event_type TEXT NOT NULL
- event_subtype TEXT NOT NULL
- player_id INTEGER NOT NULL
- team_id INTEGER NULL
- league_id INTEGER NULL
- league_label TEXT NULL
- season INTEGER NULL
- event_date TEXT NULL
- position_label TEXT NULL
- title TEXT NOT NULL
- context_text TEXT NULL
- structured_context_json TEXT NULL
- resolution_status TEXT NOT NULL
- source_ref TEXT NULL
- created_at TEXT NOT NULL
- updated_at TEXT NOT NULL
```

Use a logical uniqueness constraint sufficient for safe idempotency. For message-backed events, the canonical identity should include message/source ID + player + subtype.

Requirements:
- first-run historical backfill from existing `message*.txt`;
- subsequent incremental scan;
- repeated scan is idempotent;
- same source ID + same signature -> skip;
- changed source signature -> update/re-evaluate;
- do not delete unrelated history records when one parser family rebuilds.

`messages.dat` may enrich metadata but must remain optional if the text source proves the event.

Add useful indexes for player/date/event type/source identity.

Existing DB migration must be safe.

---

# Part B — Shared message scanner/parser foundation

Implement a reusable message source layer rather than separate file-scanning code in every feature.

Suggested modules, exact names may differ:

```text
src/ootp_milestone_tracker/importer/
  message_models.py
  message_source.py
  message_parser.py

src/ootp_milestone_tracker/history/
  history_service.py
  history_renderer.py
```

Responsibilities:
- discover `messages/message*.txt`;
- parse numeric message ID from filename;
- read UTF-8 / UTF-8 BOM safely;
- preserve raw source path and content signature;
- extract structured entity tags such as `<Name:player#ID>` and `<Name:team#ID>`;
- expose normalized raw-message object to event-specific parsers;
- centralize incremental/backfill state rather than duplicating it.

Do not assume message IDs are contiguous. A last-seen high-water mark may be used as an optimization only if the implementation still safely handles gaps/changed previously seen messages.

---

# Part C — Injury milestone parser

Implement injury occurrence milestones from message data.

Published description requirement:

`왼쪽 햄스트링 부상으로 4주 진단.`

Fallback when laterality/body location is unavailable:

`햄스트링 부상으로 4주 진단.`

Mandatory publication fields:
- diagnosis/injury name
- expected absence/diagnosis duration

If either cannot be resolved:
- preserve candidate/evidence with `resolution_status = unresolved` when useful;
- do NOT show it as a completed milestone in the normal History milestone list.

Normalize duration without changing meaning:
- days -> `N일`
- weeks -> `N주`
- months -> `N개월`
- ranges -> `N~M일/주/개월`

Do not convert months to approximate weeks or vice versa.

Best-effort optional normalization:
- left/right -> `왼쪽` / `오른쪽`
- hamstring, shoulder, back, arm, leg, etc. into concise Korean body/injury labels only when mapping is source-safe.

Injury episode identity:
- occurrence message ID should be canonical when available;
- do NOT rely only on `player_id + date` because multiple events can theoretically share a date.

IL placement/setback/return may be linked into `structured_context_json` / episode support if cheap and reliable, but only the injury occurrence creates the milestone row in Task 013.

Required tests:
- single duration
- range duration
- body side present/missing
- same-player multiple injuries
- repeat scan no duplicate
- missing injury -> unresolved/no published milestone
- missing duration -> unresolved/no published milestone

---

# Part D — MLB All-Star milestones

Only MLB/major-league All-Star selections are milestones.

Explicitly ignore:
- minor-league All-Star selections;
- fan voting updates/intermediate standings;
- nomination/candidate stories that are not final selection.

After Phase 0 proves final-source semantics:

### Fan-vote first-place selection

Preferred:

`팬 투표 1위로 NL 3루수 올스타 선정`

Required evidence:
- confirmed final MLB All-Star roster/selection;
- confirmed `*` marker semantics or equivalent source evidence;
- league identity;
- position when source provides it.

### Normal final selection

User-facing wording:

`감독 추천으로 올스타 출전`

Use this only if Phase 0 proves that non-`*` final roster members correspond to that OOTP selection semantics. If source only proves selection but not recommendation semantics, use a source-safe degraded phrase and report the discrepancy rather than fabricating manager recommendation.

Keep league/position in structured context even if the concise normal-selection text omits them.

Required tests:
- MLB fan-vote `*` positive
- MLB non-`*` positive
- minor-league All-Star rejected
- fan-vote update rejected
- repeated scan idempotent

---

# Part E — Position award parser

Implement at least:
- Platinum Stick / Silver Slugger equivalent
- Gold Glove / Golden Glove equivalent

Preferred Korean output:
- `NL 3루수 플래티넘 스틱 수상`
- `AL 투수 골든 글러브 수상`

Requirements:
- resolve winner player ID;
- resolve award season/date;
- extract league/subleague label;
- extract position when source provides it;
- normalize award display name consistently.

Do not infer a position from current player profile if the award message explicitly refers to a different award position. Source award position wins.

---

# Part F — Major voted award parser

Implement at least:
- MVP
- Cy Young
- Rookie of the Year
- Reliever of the Year / equivalent confirmed top-reliever award

Preferred forms:
- `28표로 NL MVP 수상`
- `32표 만장일치로 NL 사이영상 수상`

Requirements:
- league label when source proves it;
- winner vote count when source proves it;
- `만장일치` only when explicitly stated OR when ballot structure deterministically proves all first-place votes went to winner;
- never infer ballot count from current MLB team count or league configuration.

Safe degradation examples:
- vote unavailable -> `NL MVP 수상`
- league unavailable but award/winner certain -> `28표로 MVP 수상`

Do not discard a valid award solely because an optional fragment is missing.

---

# Part G — Monthly award parser

Implement:
- batter/player of the month -> `이달의 타자 (6월) 선정`
- pitcher of the month -> `이달의 투수 (7월) 선정`
- rookie of the month -> `이달의 신인 (5월) 선정`

Resolve month from explicit message semantics/date. Do not derive month only from filename/message ordering.

If OOTP distinguishes hitter/player naming by league, normalize user-facing Korean text to the three forms above while keeping original subtype/raw evidence in structured context.

---

# Part H — Manual quick-add league-leading awards

Implement a compact PySide6 dialog for awards that cannot be reliably automated from messages.

Suggested entry point on Milestones History/Awards tab:

`[수동 수상 기록 추가]`

Primary flow:
1. player search/select
2. season select (default latest finalized season when possible)
3. award type select
4. review auto-filled league/stat/description
5. Save

The common successful path should not require manual typing of the stat value.

Supported batter award types:
- AVG / 타격왕
- H / 안타왕
- OBP / 출루왕
- HR / 홈런왕
- RBI / 타점왕
- SB / 도루왕
- R / 득점왕
- OPS / OPS 1위

Supported pitcher award types:
- W / 다승왕
- ERA / ERA 1위
- IP / 최다이닝 1위
- SO / 탈삼진왕
- SV / 구원왕
- HOLD / 홀드왕
- WPCT / 승률 1위

Auto-fill from finalized/reconciled `batting_seasons` / `pitching_seasons` whenever possible.

Formatting examples:
- `시즌 타율 .369로 NL 타격왕 수상`
- `시즌 221안타로 NL 안타왕 수상`
- `시즌 출루율 .452로 NL 출루왕 수상`
- `시즌 58홈런으로 AL 홈런왕 수상`
- `시즌 141타점으로 AL 타점왕 수상`
- `시즌 67도루로 NL 도루왕 수상`
- `시즌 132득점으로 NL 득점왕 수상`
- `시즌 OPS 1.114로 NL OPS 1위 수상`
- `시즌 23승으로 AL 다승왕 수상`
- `시즌 ERA 0.98로 NL ERA 1위 수상`
- `시즌 242.1이닝으로 AL 최다이닝 1위 수상`
- `시즌 311탈삼진으로 NL 탈삼진왕 수상`
- `시즌 54세이브로 AL 구원왕 수상`
- `시즌 38홀드로 NL 홀드왕 수상`
- `시즌 승률 .833으로 AL 승률 1위 수상`

If league cannot be auto-resolved, show a compact league selector/override.
If finalized stat value is unavailable, allow explicit manual value only with clear manual-source marking.
If selected season is still `live`, require explicit confirmation before saving a final league-title award.

Deterministic duplicate identity:
`player_id + season + league + award subtype + source_mode=manual_user`

Saving the same logical title twice must not create duplicates.

---

# Part I — Milestones UI integration

Do not add a top-level menu.

Add an internal tab/section under Milestones, recommended name:

`History / Awards`

Minimum columns:
- Date/Season
- Player
- Type
- Description
- Source

Types in this task:
- Injury
- All-Star
- Award
- Monthly Award
- Manual League Title

Requirements:
- tracked-team-only / all-team filtering consistent with existing page;
- search by player/description/type;
- automatic vs manual source visibly distinguishable but not visually noisy;
- unresolved injury candidates are hidden from the normal published list unless an explicit debug/detail surface exists;
- no major visual redesign.

If a detail dialog already fits the existing context pattern, expose structured/raw evidence there; otherwise table context is sufficient for Task 013.

---

# Part J — Backfill / incremental service integration

Provide one service method that can be called by the existing update/refresh workflow to scan history messages.

Expected behavior:

```text
first connection / explicit rebuild
  -> historical message backfill
  -> parse Task013 event families
  -> persist idempotently

later refresh
  -> inspect new/changed message files
  -> parse only supported Task013 families
  -> update History/Awards view
```

Do not make transactions visible yet even if the generic scanner sees them. They remain unparsed/ignored until the next task.

Add a safe explicit rebuild/rescan path in Tools or existing update workflow if needed for validation, but avoid adding another top-level navigation item.

---

# Validation

Local only. No PR, no remote CI, no push.

## Static/regression
- compileall PASS
- all existing pytest PASS
- 7,682 game-box full-save scan unchanged, 0 parser failures
- game/season/career milestone identities unchanged

## Message pipeline
- full historical scan completes
- repeated historical scan idempotent
- incremental new-message scan works
- changed known message update behavior works

## Awards real-save audit
At minimum sample/verify source parity for:
- 10 MVP/Cy/ROTY/reliever-type winners combined
- 10 position awards
- 10 monthly awards
- available MLB All-Star fan-vote `*` cases
- available MLB All-Star non-`*` cases
- at least 10 minor-league All-Star records rejected
- at least 10 fan-voting update records rejected

## Injury real-save audit
At minimum:
- 20 injury occurrence samples
- diagnosis parity
- duration parity
- side/body-part optional extraction parity
- no duplicate milestone from IL/activation for same episode

## Manual league title fixtures
Prove all supported award types render correctly from season values.
Prove:
- finalized season auto-fill
- live season confirmation
- manual league override
- manual value fallback
- duplicate prevention
- save/cancel behavior

## GUI smoke
- History/Awards tab opens
- filters/search work
- manual award dialog opens
- common 4-step quick-add flow works
- table refreshes immediately after save/rescan

---

# Required report

```text
RESULT: PASS | FAIL

MESSAGE PIPELINE
- historical backfill: PASS/FAIL
- incremental scan: PASS/FAIL
- changed-message update: PASS/FAIL
- idempotency: PASS/FAIL

INJURIES
- occurrence parsing: PASS/FAIL
- diagnosis required: PASS/FAIL
- duration required: PASS/FAIL
- laterality/body-part optional: PASS/FAIL
- episode duplicate prevention: PASS/FAIL
- description rendering: PASS/FAIL

ALL-STAR
- MLB final selection: PASS/FAIL
- fan-vote `*` semantics: PASS/FAIL/UNSUPPORTED
- non-star selection semantics: PASS/FAIL/UNSUPPORTED
- minor-league exclusion: PASS/FAIL
- voting-update exclusion: PASS/FAIL

AWARDS
- position awards: PASS/FAIL
- MVP/Cy/ROTY/reliever: PASS/FAIL
- vote count: PASS/FAIL/NO SAMPLE
- unanimity: PASS/FAIL/NO SAMPLE
- monthly awards: PASS/FAIL

MANUAL LEAGUE TITLES
- batter types: PASS/FAIL
- pitcher types: PASS/FAIL
- finalized stat auto-fill: PASS/FAIL
- league auto-fill/override: PASS/FAIL
- duplicate prevention: PASS/FAIL

GUI
- history tab: PASS/FAIL
- search/filter: PASS/FAIL
- quick-add dialog: PASS/FAIL
- immediate refresh: PASS/FAIL

REAL SAVE AUDIT
- messages scanned: <n>
- published history milestones: <n>
- unresolved candidates: <n>
- source parity: PASS/FAIL

REGRESSION
- compile: PASS/FAIL
- tests: PASS/FAIL
- game full-save scan: PASS/FAIL
- parser failures: <n>

FIXES
- NONE or list

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE or exact blockers
```

Suggested commit:

`feat: add award all-star and injury history milestones`
