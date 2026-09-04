# History Milestone Design — Awards, All-Star, Injuries, Manual League Leaders

## Scope

This phase adds player-history milestones that are not derived from game/season/career stat thresholds.

Included now:
- injury occurrence milestones
- MLB All-Star milestones
- automatic award milestones
- monthly award milestones
- quick manual entry for league-leading/stat-title awards that OOTP messages do not reliably expose

Explicitly excluded from this phase:
- trades / FA signings / purchases / waiver / release / contract extensions
- retirement / Hall of Fame / draft / debut / call-up-demotion timeline UI

Transactions are the next phase after this one.

## Source model

Primary automatic source:

`<save>/messages/message*.txt`

`messages.dat` is auxiliary metadata/index evidence only. Do not make the feature depend on parsing the binary file when the text message already contains the required event evidence.

Persist parsed history events in a canonical history-event model rather than inserting ad-hoc strings directly into existing game/season/career achievement tables. The milestone UI may project/query these history events.

Recommended canonical event identity:

`source_family + source_event_id + player_id + event_subtype`

For messages, `source_event_id = msg_<message_id>`.

Existing source event + same content signature => skip.
Existing source event + changed signature => update/re-evaluate.

Historical backfill and incremental scans must be idempotent.

## Canonical history event fields

At minimum preserve:
- source_family
- source_event_id
- source_signature
- event_type (`AWARD`, `ALL_STAR`, `INJURY`)
- event_subtype
- player_id
- team_id nullable
- league_id nullable
- league_label nullable (`AL`, `NL`, custom major league label)
- season
- event_date nullable
- position_label nullable
- context_text
- structured_context_json
- source_ref
- resolution_status
- source_mode (`automatic_message`, `manual_user`)

For injuries, preserve an episode key / occurrence message ID so later IL/return tracking can extend the same episode without creating duplicate injury milestones.

## Injury milestones

Only the injury occurrence is shown as the milestone in this phase. IL placement, setback and activation may be preserved as episode evidence for future timeline work, but must not create duplicate injury milestones.

A published injury milestone requires BOTH:
1. a resolvable injury/diagnosis name;
2. a resolvable estimated absence/diagnosis duration.

If either is missing, persist an unresolved candidate if useful, but do not publish a completed milestone description.

### Required Korean description

Preferred:

`왼쪽 햄스트링 부상으로 4주 진단.`

Body side/body part is optional when the source cannot prove it:

`햄스트링 부상으로 4주 진단.`

Duration is mandatory.

Normalize common duration forms while preserving meaning:
- `4 weeks` -> `4주`
- `5-6 weeks` -> `5~6주`
- `2 months` -> `2개월`
- `5-6 months` -> `5~6개월`
- `10 days` -> `10일`

Do not invent an exact duration from vague phrases. Handle explicit season-ending/career-ending wording only when the source provides it, using a clear localized form rather than fabricating weeks/months.

Laterality/body-part extraction is best-effort. Examples of optional normalized fragments include `왼쪽`, `오른쪽`, `다리`, `팔`, `어깨`, `허리`, but omission is preferred to guessing.

## MLB All-Star milestones

Minor-league All-Star selections must NOT be stored as milestones.

Only confirmed major-league All-Star roster selections/appearances are eligible.

Do not treat fan-voting update/news messages as final selections.

Before relying on the `*` marker, verify its exact semantics in real save samples. Once confirmed:
- `*` / fan-vote first-place selection -> `팬 투표 1위로 NL 3루수 올스타 선정`
- non-`*` final major-league roster selection -> `감독 추천으로 올스타 출전`

For fan-vote first-place wording, league label and position are required when available from the final roster source. If one cannot be proven, degrade only the missing fragment rather than inventing it.

Major/minor classification must be source-backed. Prefer explicit major-league identity or existing league-level mapping. Unknown league level must not be silently treated as MLB.

## Automatic award milestones

### Position awards

Supported families include:
- Platinum Stick / Silver Slugger equivalent
- Gold Glove / Golden Glove equivalent

Preferred descriptions:
- `NL 3루수 플래티넘 스틱 수상`
- `AL 투수 골든 글러브 수상`

Extract and preserve league + position from source when available.

### Major voted awards

Supported families include at least:
- Rookie of the Year
- Reliever of the Year / top reliever award
- Cy Young
- League MVP

Preferred descriptions:
- `28표로 NL MVP 수상`
- `32표 만장일치로 NL 사이영상 수상`

Vote count must come from source evidence. Add `만장일치` only when the source proves unanimity (explicit wording or deterministic ballot evidence). Do not infer unanimity from team count or configured league size.

If vote count cannot be proven, omit the vote-count fragment rather than inventing it.

### Monthly awards

Supported:
- Player/Batter of the Month
- Pitcher of the Month
- Rookie of the Month

Preferred descriptions:
- `이달의 타자 (6월) 선정`
- `이달의 투수 (7월) 선정`
- `이달의 신인 (5월) 선정`

Month should be resolved from explicit message semantics/date. Do not guess from file order alone.

## Manual quick-entry league leaders / stat titles

OOTP messages do not reliably provide all league-leading titles, so these are intentionally user-assisted rather than guessed automatically.

Supported batter titles:
- batting champion / AVG
- hits leader / H
- OBP leader
- HR leader
- RBI leader
- SB leader
- runs leader
- OPS leader

Supported pitcher titles:
- wins leader
- ERA leader
- innings leader
- strikeout leader
- saves leader
- holds leader
- winning percentage leader

### UX goal

The common path should require roughly:

`선수 선택 -> 시즌 선택 -> 수상 종류 선택 -> 저장`

The app should auto-fill where possible:
- player ID from searchable player selector
- latest/finalized season default
- league/subleague from the player's season/team context
- exact season stat value from `batting_seasons` / `pitching_seasons`
- generated Korean description

Only expose correction fields when auto-resolution is missing or wrong.

Suggested entry point in Milestones/History area:

`[수동 수상 기록 추가]`

### Auto-generated examples

- AVG: `시즌 타율 .369로 NL 타격왕 수상`
- H: `시즌 221안타로 NL 안타왕 수상`
- OBP: `시즌 출루율 .452로 NL 출루왕 수상`
- HR: `시즌 58홈런으로 AL 홈런왕 수상`
- RBI: `시즌 141타점으로 AL 타점왕 수상`
- SB: `시즌 67도루로 NL 도루왕 수상`
- R: `시즌 132득점으로 NL 득점왕 수상`
- OPS: `시즌 OPS 1.114로 NL OPS 1위 수상`
- W: `시즌 23승으로 AL 다승왕 수상`
- ERA: `시즌 ERA 0.98로 NL ERA 1위 수상`
- IP: `시즌 242.1이닝으로 AL 최다이닝 1위 수상`
- SO: `시즌 311탈삼진으로 NL 탈삼진왕 수상`
- SV: `시즌 54세이브로 AL 구원왕 수상`
- HOLD: `시즌 38홀드로 NL 홀드왕 수상`
- WPCT: `시즌 승률 .833으로 AL 승률 1위 수상`

Use finalized/reconciled season values when available. If only live values exist, make the state clear and require user confirmation before storing a final league-title record.

Manual duplicate identity should be deterministic, e.g. player + season + league + award subtype. Re-saving the same logical title must update or reject, never duplicate silently.

## UI integration

Do not add a new top-level navigation item.

Add a compact History/Awards area under the existing Milestones page or an equivalent internal tab.

Minimum table fields:
- Date/Season
- Player
- Type
- Description
- Source

Support tracked-team filtering consistently with existing milestone pages.

Automatic and manual entries should be visually distinguishable by source but share the same description renderer/output style.

## No-fabrication rule

If a required semantic field is not provable, either:
- omit an optional fragment; or
- keep the candidate unresolved and do not publish the milestone when the field is mandatory.

Mandatory for injury publication: injury + duration.
Mandatory for fan-vote wording: confirmed final MLB All-Star selection and confirmed fan-vote-first marker semantics.
Mandatory for manual league-title entry: player + season + award type; value should come from finalized season data or explicit user override.
