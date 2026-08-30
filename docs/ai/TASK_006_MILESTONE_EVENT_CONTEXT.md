# Task 006 — Resolve Milestone Achievement Game Context

## Goal

After Task 005 can import authoritative numeric player stats and detect threshold crossings, enrich each newly crossed milestone with the exact game/date/situation when the local OOTP sources make that resolvable.

Primary enrichment sources:

```text
news/html/box_scores/game_box_*.html
news/txt/leagues/log_*.txt
messages/message*.txt
```

Do not change numeric milestone values from these sources. `player_*_stats.txt` remains the numeric source of truth.

## Read first

- `docs/MILESTONE_ACHIEVEMENT_MODEL.md`
- `docs/MILESTONE_RULES_DESIGN.md`
- `docs/OOTP_DATA_IMPORT_PLAN.md`
- `docs/research/OOTP27_SOURCE_INVENTORY_LOCAL.md`
- Task 005 implementation/schema after it passes

## Required resolution fields

Resolve as many as the source actually proves:

```text
game_id
game_date
competition_type
team_id
opponent_team_id
opponent_player_id
player_game_number
team_game_number
inning
inning_half
score_for
score_against
outs
base_state
play_result
context_text
source_file
```

Unresolvable values stay NULL. Never infer exact details from names or approximate timing.

## Game count semantics

This is mandatory:

- Career milestone: `player_game_number` = player's career games played in the same `competition_type` at achievement time.
- Season milestone: `player_game_number` = player's season games played in the same season + `competition_type` at achievement time.

Regular season, postseason, spring training, and international game counts must never be mixed.

## Resolution strategy

For a crossing found between two imports:

```text
previous snapshot -> current snapshot
```

1. Determine the changed stat delta and competition type.
2. Determine the candidate date/game interval between imports.
3. Search candidate game boxes for the player ID and relevant stat change.
4. Use game box to establish game ID/date/opponent and game-level stat line.
5. If multiple candidate games remain, use logs to locate the exact play crossing the threshold.
6. Resolve opponent player when the play log identifies the batter/pitcher counterpart.
7. Use messages only as an optional corroborating source for date/entity/text.
8. Mark `resolved_play`, `resolved_game`, or leave `unresolved`.

If the user imports infrequently and multiple games make the exact crossing ambiguous, do not guess.

## Parser boundaries

Recommended modules:

```text
importer/game_box_parser.py
importer/game_log_parser.py
importer/message_parser.py
milestones/achievement_resolver.py
```

Parsers return structured source records. Resolver joins them to unresolved achievement rows.

## Idempotency

Re-running resolution must update the same achievement row, not create a second event.

## UI integration

Minimal only. In the Milestones/Player detail view, a resolved achievement may show compact context such as:

```text
3,000 H · 2034-08-17 vs BUS
Career Game 2,184 · 7th · Single off <pitcher>
```

Show only fields that exist.

## Validation

Local only:

1. Choose at least one real player/game where a known stat increment can be located in both aggregate stats and box/log files.
2. Verify player ID join.
3. Verify game ID/date/opponent.
4. Verify competition type.
5. Verify game-number semantics.
6. Verify exact play/opponent player when available.
7. Verify unresolved behavior for intentionally ambiguous interval.
8. Verify repeated resolution is idempotent.
9. Existing tests remain green.

## Git/cost rules

- No remote push from local worker.
- No PR.
- No GitHub Actions.
- One final local feature commit after validation when possible.

Suggested commit:

```text
feat: resolve milestone achievement game context
```

## Report format

```text
RESULT: PASS | FAIL

RESOLUTION
- achievements tested: <n>
- resolved_play: <n>
- resolved_game: <n>
- unresolved: <n>

CHECKS
- box parser: PASS/FAIL
- log parser: PASS/FAIL
- message parser: PASS/FAIL/SKIPPED
- player/game joins: PASS/FAIL
- competition separation: PASS/FAIL
- game-count semantics: PASS/FAIL
- opponent player: PASS/FAIL/NOT_AVAILABLE
- idempotency: PASS/FAIL
- GUI smoke: PASS/FAIL

LIMITATIONS
- <only real source limitations>

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE or <exact blocker>
```
