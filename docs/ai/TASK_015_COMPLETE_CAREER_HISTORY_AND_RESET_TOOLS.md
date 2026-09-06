# Task 015 — Complete Career History + Reset Tools

## Goal

Finish the remaining player-career history features on top of Tasks 013–014, then add safe database reset tools so the real OOTP save can be parsed repeatedly during the next audit task.

This is the **feature-completion task**. Do not perform the final end-to-end correctness audit here beyond the validation required to finish implementation. Task 016 will perform the product-level real-save audit after this task passes.

Repository: `Arktis-P/OOTP-Milestone-Tracker-V0.2`
Branch: `user/Workspace`

Read first:

- `.agents/rules/workflow.md`
- `docs/research/OOTP27_PLAYER_HISTORY_SOURCE_RESEARCH_LOCAL.md`
- `docs/HISTORY_MILESTONE_DESIGN.md`
- `docs/TRANSACTION_HISTORY_DESIGN.md`
- `docs/CAREER_AND_CONTEXT_DESIGN.md`
- `docs/REAL_SAVE_AUDIT_AND_RESET_DESIGN.md`
- `docs/ai/TASK_016_END_TO_END_REAL_SAVE_AUDIT.md`

Preserve all Task 006–014 behavior and existing source-safe/no-fabrication rules.

---

# Part A — Injury episode tracking

Task 013 already publishes the injury occurrence milestone. Extend this to a durable episode model rather than creating unrelated rows for each follow-up message.

Recommended model:

```text
injury_episodes
injury_episode_events
```

Canonical episode identity should be based on the original injury occurrence message ID when available. Do not use only `player_id + date` as the primary identity.

Track, when provable:

- player_id
- original occurrence message ID
- occurrence date
- diagnosis
- optional laterality/body part
- original expected duration
- current expected duration / updated prognosis
- IL placement
- setback / recovery delay
- rehab/return update
- activation / return
- episode status: active / recovered / unresolved
- source refs for every episode event

The public milestone/history occurrence title remains the existing Task 013 description, e.g.:

`왼쪽 햄스트링 부상으로 4주 진단.`

Follow-up episode events should be visible in details/timeline without duplicating the original injury milestone. Use concise descriptions such as:

- `15일 부상자 명단 등록`
- `복귀 예상 2주 연장`
- `부상 복귀`

Only render details proven by the source. Minor day-to-day injuries without explicit return messages may remain closed only when there is deterministic evidence; otherwise retain an unresolved/estimated state instead of fabricating a return date.

Episode rebuild/backfill must be idempotent.

---

# Part B — Other confirmed career events

Implement the source-confirmed event families from Task 012 using `player_history_events` and the existing message pipeline.

## 1. Major League debut

Track only actual major-league debut, not minor-league first appearances.

Default title:

`MLB 데뷔`

If team/opponent/date are provable, store them in structured context. Do not require them in the compact title.

Deduplicate message evidence and any stats/game-derived fallback so one debut produces one canonical history event.

## 2. Draft

Use the highest-authority source available from research (`message*.txt`, draft log/history fallback where necessary).

Preferred title when all fields are known:

`신인 드래프트 1라운드 3순위 지명`

Store team, league, year, round, overall/round pick when provable. Omit unknown fragments instead of guessing.

## 3. Retirement

Default title:

`현역 은퇴`

Store retirement date/season, last known team and age only when source-proven. Retirement does **not** trigger career rate milestones; retirement-rate tracking remains out of scope.

## 4. Hall of Fame

Default title:

`명예의 전당 헌액`

If voting percentage is explicitly available, use e.g.:

`92.4% 득표로 명예의 전당 헌액`

Never infer voting percentage.

## 5. MLB call-up / option / demotion

Track only moves meaningful to major-league career history. Avoid noisy minor-to-minor roster shuffling.

Examples:

- `MLB 콜업`
- `AAA로 옵션`
- `마이너리그 강등`

Use the exact level/team only when explicit. Prevent duplicate records where the same move is announced in multiple messages.

---

# Part C — Secondary transaction events

Task 014 intentionally left these unresolved:

- waiver
- release
- DFA
- roster move

Implement them only after inspecting actual local message samples and proving deterministic patterns.

Suggested normalized subtypes:

- `WAIVER_CLAIM`
- `RELEASE`
- `DFA`
- roster movement should reuse the MLB call-up/option/demotion family from Part B rather than duplicate it under transactions.

Preferred compact descriptions:

- `웨이버 클레임으로 LAD 이적`
- `NYY에서 방출`
- `지명할당`

If team identity cannot be proven, omit the team fragment.

Do not implement `PURCHASE` unless an actual source sample is found and documented. `NOT AVAILABLE IN SAMPLE` is an acceptable final state.

---

# Part D — Unified player career history UI

Do not add a new top-level navigation item.

Finish the existing History area so the application can inspect a player's career chronology in one place.

At minimum:

1. Existing Milestones > History tab supports these filters:
   - all
   - injury
   - all-star
   - award / monthly award / manual league title
   - transaction / contract
   - debut
   - draft
   - retirement
   - Hall of Fame
   - roster move
2. Search continues to work by player and description.
3. Tracked-team-only filtering uses event-time semantics where possible, not only current team membership.
4. A selected player can be viewed as a chronological career history list/timeline using the existing Player Records/detail surface. Keep it compact; no major visual redesign.
5. The same canonical event must not appear twice because it is accessible from two UI surfaces.
6. Injury episode detail should expose its follow-up events without publishing duplicate injury milestones.

Preferred chronological row fields:

```text
Date | Type | Description | Team | Source
```

---

# Part E — Safe reset tools for repeated real-save testing

The next task needs to repeatedly clear parsed results and run the application from a known state. Add explicit reset actions to `도구` / Tools.

## Reset 1 — History / Message Tracking Reset

Purpose: cheaply retest `message*.txt` parsing without destroying game/season/career ledger data.

Delete/reinitialize all automatic message-derived state, including:

- automatic `player_history_events` (`source_family = MESSAGES`)
- `transaction_events`
- `transaction_participants`
- `injury_episodes`
- `injury_episode_events`
- message scan cursor/state if one exists

Preserve by default:

- manual league-title entries
- app settings
- tracked-team choice
- player Korean-name mappings
- Game Ledger
- season/career checkpoints and milestones

Provide an explicit checkbox/secondary confirmation if the user also wants to delete manual history entries.

After reset, the next full history scan must process all historical messages again.

## Reset 2 — All Parsed Tracking Data Reset

Purpose: perform a clean end-to-end import without deleting user configuration.

Transactionally clear all source-derived/aggregate tracking results, including the relevant rows from:

- Game Ledger (`games`, player game rows, game events)
- game achievements
- season aggregates/state/reconciliation/achievements
- career checkpoints/achievements
- history/transactions/injury episodes
- import/checkpoint scan state that would cause source files to be skipped
- other derived milestone result tables that would leave stale product output

Preserve:

- `app_settings`
- save-path configuration
- milestone rule settings/custom thresholds
- tracked-team configuration
- user-entered Korean name mappings when technically possible
- source files on disk (never modify the OOTP save)

Inspect actual ownership before deciding whether `players` / `teams` should be retained. Prefer retaining stable identity/name mapping rows if the normal import path can safely reuse them. The reset must leave the DB in a state that the normal application import workflow can rebuild deterministically.

## Reset 3 — Factory/sample reset

Keep the existing `Reset generated sample database` behavior separate. It is not a substitute for the two OOTP-test resets above.

## Safety/UX requirements

- Show a destructive-action confirmation naming exactly what will be deleted/preserved.
- Show row-count summary before or after reset.
- Run deletion in a DB transaction.
- On failure rollback completely.
- Immediately refresh all affected pages.
- Never delete or modify the user's `.lg` save files.
- Reset action itself must be idempotent.

---

# Part F — Product-level import actions

Task 016 must be able to execute the real workflow through the app, not only Python diagnostics.

Ensure Tools or the existing appropriate product surface exposes working actions for:

- full/update Game Ledger import
- full history/message scan
- incremental history/message scan
- history reset
- all parsed tracking reset

Do not duplicate buttons if equivalent actions already exist elsewhere; wire to the same services.

Each action should return a concise result summary with scanned/inserted/updated/unresolved counts.

---

# Part G — Validation for feature completion

Run locally only. No PR, GitHub Actions, or remote CI.

Required:

1. `compileall` PASS
2. all existing tests PASS
3. new fixtures for injury episode linkage PASS
4. fixtures for debut/draft/retirement/HOF/MLB roster moves PASS
5. deterministic waiver/release/DFA samples PASS if implemented
6. reset-history twice PASS
7. reset-all-tracking twice PASS
8. reset then history full scan PASS
9. reset then normal Game Ledger import PASS
10. full-save game scan remains 0 parser failures
11. no regression to Tasks 006–014

Real-save validation in this task is for implementation confidence only. The exhaustive record-by-record audit belongs to Task 016.

---

# Required report

```text
RESULT: PASS | FAIL

INJURY EPISODES
- occurrence linkage: PASS/FAIL
- IL linkage: PASS/FAIL/NO SAMPLE
- setback linkage: PASS/FAIL/NO SAMPLE
- activation/return linkage: PASS/FAIL/NO SAMPLE
- duplicate prevention: PASS/FAIL

OTHER CAREER EVENTS
- MLB debut: PASS/FAIL/NO SAMPLE
- draft: PASS/FAIL/NO SAMPLE
- retirement: PASS/FAIL/NO SAMPLE
- Hall of Fame: PASS/FAIL/NO SAMPLE
- MLB call-up/option/demotion: PASS/FAIL/NO SAMPLE

SECONDARY TRANSACTIONS
- waiver: PASS/FAIL/UNRESOLVED
- release: PASS/FAIL/UNRESOLVED
- DFA: PASS/FAIL/UNRESOLVED
- purchase: PASS/FAIL/NOT AVAILABLE

CAREER HISTORY UI
- filters/search: PASS/FAIL
- player chronology: PASS/FAIL
- event-time tracked filtering: PASS/FAIL
- injury details: PASS/FAIL

RESET TOOLS
- history reset: PASS/FAIL
- preserve manual/settings/mappings: PASS/FAIL
- all tracking reset: PASS/FAIL
- source files untouched: PASS/FAIL
- repeated reset: PASS/FAIL

PRODUCT IMPORT ACTIONS
- full/update games: PASS/FAIL
- full history scan: PASS/FAIL
- incremental history scan: PASS/FAIL
- result summary: PASS/FAIL

REGRESSION
- compile: PASS/FAIL
- tests: PASS/FAIL (<n>/<n>)
- full-save game scan: PASS/FAIL
- parser failures: <n>

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE or exact blockers
```

Suggested feature-complete commit:

`feat: complete player career history and reset tools`

Do not push from the local worker unless the user's current workflow explicitly instructs it. Checkpoint commits remain local.