# Career Tracking & Milestone Context Design

## Scope

This document defines career aggregation, career milestones, the season BB extension, and canonical context rendering for game/season/career/team achievements.

Career rate milestones at retirement are intentionally out of scope. The current sources do not provide a reliable retirement checkpoint that can be tied to a final exported rate line without user intervention.

## Career aggregate model

Career current value = latest reconciled career checkpoint from `player_*_stats.txt` + all processed game deltas after that checkpoint for the same `competition_type`.

Never merge `regular_season`, `postseason`, `spring_training`, or `international`.

When a new end-of-season export is reconciled, store the official OOTP career totals as a new checkpoint and preserve adjustment history rather than silently overwriting the prior computed value.

## Career milestone defaults

### Batter

- Games appeared: 1000, 1500, 2000, 2500, 3000
- Hits: start 1500, step +500
- Home runs: start 200, step +100
- Runs: start 750, step +250
- RBI: start 750, step +250
- Stolen bases: start 200, step +100
- Walks: start 1000, step +500

### Pitcher

- Games appeared: 200, 300, 400, 500, 600, 700
- Games started: 200, 250, 300, 350, 400, 450, 500
- Innings pitched: start 1500 IP, step +500 IP
- Strikeouts: start 1500, step +500
- Wins: start 100, step +50
- Holds: start 100, step +25
- Saves: start 200, step +50

Open-ended start/step ladders must not have an artificial hard maximum. Generate the next threshold as required.

## Season BB extension

Add batter season walks milestones:

`50, 100, 150, 200, 250, 300 BB`

These are counting milestones and are recorded during the season at the exact threshold-crossing game, just like season H/HR/RBI/R/SB.

## Threshold crossing semantics

Season and career milestones preserve every threshold reached over time.

Example:

- Career 1500 H achieved in Game A -> preserve
- Career 2000 H achieved later in Game B -> preserve both

If one game crosses more than one configured threshold, create every newly crossed threshold unless the thresholds are within the same game-only highest-only family. Game-only highest-only suppression does not apply to season/career ladders.

## Canonical achievement evidence

Store structured evidence first, render Korean context text second. Preserve as many of the following fields as the source can prove:

- `game_id`, date, season, competition type
- player/team IDs
- opponent team/player IDs
- inning / half
- outs before play
- base state before play
- score before/after
- play result code and raw text
- batting/pitching game line
- play sequence
- pitch count when deterministic
- source/evidence quality

Never fabricate missing base state, outs, pitch count, opponent player, or hit-order details.

## Context text templates

### Batter — game milestones

- Hits: `6타수 4안타`
- RBI: `5타수 5안타 1홈런 5타점`; omit HR fragment when HR=0.
- Multi-HR: join each HR event in chronological order, e.g. `3회초 3점 홈런 & 5회초 솔로 홈런`. Use `솔로 홈런`, `2점 홈런`, `3점 홈런`, `만루 홈런`.
- Grand slam: must be a bases-loaded 4-run HR. Example: `6회말 1사 만루에서 만루 홈런`. If outs/base state cannot be proven, omit only the unproven fragments. A 3-run HR with runners on 1st/2nd is not a grand slam.
- Stolen bases: prefer `3출루 3도루` when total times on base can be proven; otherwise `3도루`.
- Cycle: `5타수 4안타 1홈런 사이클링 히트 (3루타 - 2루타 - 홈런 - 1루타)`. Preserve chronological hit-type order only when deterministically available; otherwise omit parentheses.

### Pitcher — game milestones

- Strikeouts: `8.0이닝 12탈삼진`
- Complete-game win: game pitching line followed by `완투승`
- Shutout win: use `무실점` rather than `0실점`, followed by `완봉승`
- No-hit no-run: use `무피안타 무실점 ... 노히트 노런 승리`
- Perfect game: use `무피안타 무실점 ... 퍼펙트 게임 승리`
- Omit strikeout fragment if SO=0.

### Batter — season/career counting milestones

For H/HR/RBI/R/SB/BB, resolve the exact threshold-crossing play when possible by combining the pre-game total with ordered play events.

- Hit: `1회초 무사 3루에서 1타점 1루타`; omit outs/base/RBI fragments when unavailable/not applicable.
- HR: `3회초 2사 3루에서 2점 홈런`
- RBI: `4회초 1사 2,3루에서 2타점 2루타`
- Run: `5회초 2사 3루, {batter_name}의 1루타로 득점`; if cause/batter cannot be proven, render only the resolved scoring context.
- SB: `6회초 무사 1루, {batter_name} 타석에 2루 도루`; use `3루 도루` when applicable.
- BB: `7회초 무사에서 7구 볼넷 출루`; omit pitch count if unavailable.
- Games appeared: use that game batting line, e.g. `2타수 1안타`.

### Batter — season final rate milestones

Season only; no career/retirement rate milestones.

- AVG: `시즌 타율 .390`
- OBP: `시즌 출루율 .451`
- OPS: `시즌 OPS 1.123`

Use the exact finalized/reconciled season value.

### Pitcher — season/career milestones

- IP: game line fragment, e.g. `5.0이닝 투구`
- SO: exact threshold strikeout play when available, e.g. `1회말 무사 3루 2-3에서 6구 헛스윙 삼진`
- Win: `5.1이닝 3피안타 1실점 9탈삼진 승리`
- Hold/Save: `1.0이닝 1피안타 무실점 홀드` / `... 세이브`
- Games started: `6.2이닝 3피안타 1실점 10탈삼진 투구`; use `승리` instead of `투구` when the pitcher earned the win.
- Games appeared: `1.1이닝 1피안타 무실점 홀드`; if no W/HLD/SV decision applies, end with `투구`.

### Pitcher — season final rate milestones

- ERA: `시즌 ERA 1.99`
- FIP: `시즌 FIP 1.89`

FIP remains unavailable unless a trustworthy source or verified formula input is established. Do not fabricate it.

### Team

- Starters/all appearing hit or RBI: `선발 (홍창기-박해민-딘-문보경-송찬의-박동원-오지환-문성주-신민재) 전원 안타`; substitute `출장` / `타점` as appropriate.
- Team win counting milestone: `9-3 승리`
- Postseason berth/division title: `120승 33패로 포스트 시즌 진출` / corresponding division-title text.
- WCS/DS/LCS/WS title: `시리즈 3승 2패로 디비전 시리즈 우승`

Existing team game pitching milestones also need canonical context even though the user did not provide examples:

- Team shutout: `{score} 승리 · 팀 완봉승`
- Team no-hit no-run: `{score} 승리 · 팀 노히트 노런`; include `합작` when multiple pitchers participated.
- Team perfect game: `{score} 승리 · 팀 퍼펙트 게임`

## Context resolution quality

Use explicit statuses, e.g.:

- `play_resolved`: exact play/event found
- `game_resolved`: achievement game and game line known, exact play not required or not resolvable
- `final_export`: season-final rate/checkpoint milestone
- `partial`: some requested context fields unavailable

A partial context is acceptable; invented context is not.
