# Task 011 — Career Milestones & Unified Context Resolver

## Goal

Implement career aggregation and career milestones on top of the completed season/checkpoint pipeline, add season BB milestones, and unify context/evidence generation across game, season, career, and team achievements.

Do not implement retirement-rate milestones. Do not start awards/injury/transaction tracking in this task.

Read first:

- `docs/CAREER_AND_CONTEXT_DESIGN.md`
- `docs/SEASON_TRACKING_DESIGN.md`
- `docs/OOTP_DATA_IMPORT_PLAN.md`
- `docs/GAME_MILESTONE_CATALOG.md`
- `docs/research/OOTP27_SEASON_STATS_RESEARCH_LOCAL.md`
- `.agents/rules/workflow.md`

Preserve all existing Task 006–010 behavior and tests.

## Part A — Season BB extension

Add season batter BB counting milestones:

`50 / 100 / 150 / 200 / 250 / 300`

Requirements:

- evaluate after each regular-season game ledger update;
- preserve every threshold reached over the season;
- exact threshold-crossing game must be stored;
- resolve exact threshold walk event from log when possible;
- context should prefer `N회초/말 [아웃]에서 [구수]구 볼넷 출루`; omit pitch count/outs if unavailable;
- add these values to season milestone settings using the same persistence/edit/reset model as the existing season counting thresholds.

## Part B — Career checkpoint and aggregation

Implement a durable career checkpoint model using the player stats export already supported by Task 010.

Career current state must be:

`latest reconciled career checkpoint + post-checkpoint game ledger deltas`

Requirements:

1. Preserve checkpoint metadata, source signature/date, competition type, and represented-game cutoff/snapshot.
2. Never double-count games represented by a checkpoint.
3. Keep regular season/postseason/spring/international isolated.
4. When an end-of-season export is reconciled, create/update the next official career checkpoint and preserve adjustment history.
5. Rebuild must be deterministic and idempotent.
6. Mid-season checkpoint/reconciliation must not corrupt historical career milestone timing.
7. Career aggregate should expose at least all currently safely supported cumulative fields, not only milestone fields.

## Part C — Career appearance counts

Implement career counts from checkpoint + game ledger:

### Batter
- games appeared: `1000 / 1500 / 2000 / 2500 / 3000`

### Pitcher
- games appeared: `200 / 300 / 400 / 500 / 600 / 700`
- games started: `200 / 250 / 300 / 350 / 400 / 450 / 500`

Research/verify how a pitching start is represented in the current parsed game source. Do not guess. If existing parser reliably identifies the starting pitcher, persist a normalized `is_starter`/GS fact in the game ledger. If not, prove a deterministic derivation from source ordering/labels before using it.

A batter game appearance uses the canonical player participation represented by the batting game ledger. If a source limitation excludes pure pinch-running/defensive-only appearances, document that limitation rather than fabricating G.

## Part D — Career milestone ladders

Implement these defaults for regular-season career milestones:

### Batter
- H: start 1500, step 500
- HR: start 200, step 100
- R: start 750, step 250
- RBI: start 750, step 250
- SB: start 200, step 100
- BB: start 1000, step 500
- G: explicit list 1000/1500/2000/2500/3000

### Pitcher
- IP: start 1500, step 500
- SO: start 1500, step 500
- W: start 100, step 50
- HOLD: start 100, step 25
- SV: start 200, step 50
- G: explicit list 200/300/400/500/600/700
- GS: explicit list 200/250/300/350/400/450/500

Open-ended start/step ladders must generate future thresholds as needed and must not stop at a hardcoded maximum.

Season/career threshold semantics differ from game highest-only semantics: preserve every distinct threshold reached over time.

If one game jumps over multiple previously-unreached career thresholds, store every crossed threshold, all linked to that achievement game. This is rare but must be correct.

## Part E — Unified achievement context model

Replace ad-hoc context creation with a shared resolver/renderer used by game, season, career, and team milestone rows.

Suggested modules:

```text
src/ootp_milestone_tracker/milestones/
├─ context_models.py
├─ context_resolver.py
└─ context_renderer.py
```

The exact layout may differ.

Persist structured evidence in addition to display text. A JSON evidence column/table is acceptable if normalized columns would be excessive, but stable identifiers and resolution status must remain queryable.

Recommended fields:

```text
resolution_status
play_sequence
inning
half
outs_before
base_state_before
score_before_home/away
score_after_home/away
opponent_team_id
opponent_player_id
play_result
pitch_count nullable
raw_context/evidence
```

Never invent missing data.

## Part F — Exact crossing-play resolution

For event-based season/career counting milestones, use pre-game aggregate + ordered events to locate the exact event that crosses the threshold.

### Batter event rules

- H: locate exact hit event; include RBI if that hit produced RBI.
- HR: locate exact HR; render solo/2-run/3-run/grand-slam from proven runner count.
- RBI: RBI may increase by >1 on one play. If the threshold falls inside that play's RBI increment, that play is the achievement context.
- R: locate exact scoring event and scoring player. Include batter/cause only when source proves it.
- SB: locate exact successful steal event and destination base; include current batter when resolvable.
- BB: locate exact walk; include pitch count only when deterministically present.

### Pitcher event/result rules

- SO: locate exact strikeout event; include batter, count, pitch number/result when resolvable.
- IP: exact play resolution is not mandatory. Achievement game + final game pitching line is sufficient unless an exact out can be resolved cleanly.
- W/HOLD/SV: game result/pitching line context is authoritative; exact play is not required.
- G/GS: achievement game line is authoritative.

When exact play cannot be resolved but achievement game is known, store `game_resolved` or `partial`, not guessed play context.

## Part G — Canonical Korean context rendering

Implement the templates in `docs/CAREER_AND_CONTEXT_DESIGN.md`.

Important formatting rules:

- halves: `1회초`, `6회말`
- outs: `무사`, `1사`, `2사`
- base state: `1루`, `1,2루`, `2,3루`, `만루`; omit if unproven
- HR runs: `솔로 홈런`, `2점 홈런`, `3점 홈런`, `만루 홈런`
- zero pitching values: prefer `무피안타`, `무실점`
- IP: baseball decimal form (`8.0이닝`, `6.2이닝`), not arithmetic decimal fractions
- omit optional fragments instead of rendering unknown placeholders

Correct grand-slam semantics are mandatory: bases loaded + 4-run HR. Do not reuse a 3-run HR example.

## Part H — Existing game/team context backfill

Using the persisted game ledger/events/log data, rebuild/backfill context for existing game achievements where possible, without duplicating achievement identities.

Ensure context coverage for currently tracked game rules:

### Batter game
- H family
- RBI family
- HR family
- SB family
- grand slam
- cycle

### Pitcher game
- SO family
- complete-game win
- shutout win
- no-hit no-run
- perfect game

### Team game
- starters/all-appeared all-hit
- starters/all-appeared all-RBI
- team shutout/no-hit-no-run/perfect game

For team batting context, include player names in batting-table order when available.

For team pitching context, use concise default forms such as `{score} 승리 · 팀 완봉승`; add `합작` for no-hit-no-run when multiple pitchers participated.

## Part I — Season/team context integration

Backfill/generate context for Task 010 season milestones:

- batter H/HR/RBI/R/SB/BB
- batter final AVG/OBP/OPS
- pitcher IP/SO/W/HOLD/SV
- pitcher final ERA/FIP when available
- team W
- postseason berth/division title/WCS/DS/LCS/WS titles

Postseason series title context should include actual series record when it can be derived/proven, e.g. `시리즈 3승 2패로 디비전 시리즈 우승`.

## Part J — UI

In Milestones views:

1. Career achievements must be filterable by scope.
2. Show rendered context consistently for game/season/career achievements.
3. Keep context concise in table; allow full details via row selection/detail pane/dialog if needed.
4. Career milestone target/progress ladder should use the same compact tracker philosophy already established.
5. Do not add a new top-level navigation item.

No major visual redesign.

## Data/settings compatibility

- Existing DBs must migrate safely.
- Existing game/season achievements must remain intact.
- Rebuild/backfill must be idempotent.
- Current game and season milestone settings must continue working.
- Season BB defaults/settings must be added without resetting user-edited existing thresholds.

## Validation

Local only. No PR / remote CI / push.

### Required regression

1. compileall PASS
2. all existing pytest PASS
3. full-save scan PASS with 0 parser failures
4. game milestone counts/identities unchanged except intentional context backfill
5. season milestone behavior unchanged except added BB

### Career aggregation fixtures

Prove:

- checkpoint + one/multiple game deltas
- regular/postseason separation
- checkpoint cutoff prevents double count
- end-season reconciliation updates next career checkpoint
- repeated rebuild is identical

### Career threshold boundaries

At minimum test values immediately below/at/above every explicit ladder edge and several generated open-ended thresholds.

Examples:

- H 1499/1500/1999/2000/2500/3000
- HR 199/200/299/300/... and a generated high threshold
- W 99/100/149/150
- HOLD 99/100/124/125
- IP using outs internally so 1499.2 -> next out -> 1500.0 is handled correctly
- batter G 999/1000/1499/1500
- pitcher G/GS boundary values

### Context fixtures

Prove positive and degraded/fallback rendering for every context family, including:

- exact hit/HR/RBI/SB/BB/SO crossing play
- multi-RBI play crossing threshold
- run scored with/without resolvable batter cause
- multi-HR chronological join
- cycle hit sequence available/unavailable
- pitching line with 0 SO omitted
- team lineup name ordering
- team combined no-hitter wording
- missing base/out/pitch count omitted rather than guessed

### Real-save audits

Use actual local save data to sample at least:

- 20 resolved batter contexts across multiple rule families
- 20 resolved pitcher contexts
- 10 team contexts
- any available season threshold crossing contexts
- career contexts if current checkpoint/sample history permits; otherwise controlled fixture plus source-parity research

Compare rendered context against original game box/log for sampled records.

## Required report

```text
RESULT: PASS | FAIL

SEASON BB
- thresholds/settings: PASS/FAIL
- crossing context: PASS/FAIL/NO SAMPLE

CAREER AGGREGATION
- checkpoint import: PASS/FAIL
- post-checkpoint deltas: PASS/FAIL
- competition separation: PASS/FAIL
- reconciliation: PASS/FAIL
- idempotency: PASS/FAIL

CAREER MILESTONES
- batter H/HR/R/RBI/SB/BB/G: PASS/FAIL
- pitcher IP/SO/W/HOLD/SV/G/GS: PASS/FAIL
- open-ended ladders: PASS/FAIL

CONTEXT
- game batter: PASS/FAIL
- game pitcher: PASS/FAIL
- game team: PASS/FAIL
- season batter: PASS/FAIL
- season pitcher: PASS/FAIL
- season team: PASS/FAIL
- career batter: PASS/FAIL
- career pitcher: PASS/FAIL
- fallback/no-fabrication: PASS/FAIL

REAL SAVE AUDIT
- samples checked: <counts>
- source parity: PASS/FAIL

GUI
- career scope/view: PASS/FAIL
- context display: PASS/FAIL

REGRESSION
- compile: PASS/FAIL
- tests: PASS/FAIL
- full-save scan: PASS/FAIL
- parse failures: <n>

FIXES
- NONE or list

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE or exact blockers
```

Suggested commit:

`feat: add career milestones and unified achievement context`
