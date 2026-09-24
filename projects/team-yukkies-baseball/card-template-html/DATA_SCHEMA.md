# TEAM YUKIES Card Template — Current Data Schema

이 문서는 `card-template-html/`의 현재 HTML/CSS/JS 구현을 기준으로 한 데이터 규칙입니다.

과거 `CARD_DATA_SCHEMA.md`는 `archive/legacy-card-template/docs/`로 이동했으며 현재 기준으로 사용하지 않습니다.

## 1. 기본 데이터

기본 레이팅 원본은 프로젝트 루트의 `../PLAYER_RATINGS.csv`입니다.

템플릿 폴더에는 테스트/확장 예시가 있습니다.

- `data/PLAYER_RATINGS.csv`
- `data/PLAYER_PROFILE_SCHEMA_SAMPLE.csv`
- `data/PLAYER_RATINGS_EXTENDED_SAMPLE.csv`
- `data/player-data.js`

## 2. 공통 카드 필드

현재 렌더러에서 사용하는 주요 필드:

- `player_id`
- `display_first_name`
- `display_last_name`
- `player_type`: `BATTER` / `PITCHER`
- `overall`
- `uniform_number`
- `primary_position`
- `scouting_report`
- `serial`

기존 CSV의 `character_name`은 선수 식별/표시 보조 정보로 유지할 수 있지만, 카드의 영문 이름을 정확히 표시하려면 `display_first_name`, `display_last_name`을 별도로 두는 것을 권장합니다.

## 3. 신상 정보

뒷면 이름/팀명 아래 3줄은 다음 원본 필드에서 자동 생성합니다.

- `height_cm` — 키
- `weight_kg` — 몸무게
- `bats` — 타격 손
- `throws` — 투구 손
- `birthday` — 생일
- `birth_place` — 태어난 곳
- `trait_1`
- `trait_2`
- `trait_3`

출력 형식:

```text
{height_cm}cm | {weight_kg}kg | Bats: {bats} | Throws: {throws}
{birthday} | {birth_place}
{trait_1} | {trait_2} | {trait_3}
```

CSV 로더는 한국어 별칭도 인식합니다.

- 키
- 몸무게
- 타격 손
- 투구 손
- 생일
- 태어난 곳
- 선수 특징 1 / 2 / 3

## 4. 타자 레이팅

상세 필드:

- `contact`
- `power`
- `gap`
- `eye`
- `baserunning`
- `stealing`
- `arm`
- `def_c`
- `def_1b`
- `def_2b`
- `def_3b`
- `def_ss`
- `def_lf`
- `def_cf`
- `def_rf`

현재 앞면 6칸은 다음 순서로 렌더링합니다.

```text
CON = contact
POW = power
GAP = gap
EYE = eye
SPD = baserunning
FLD = primary_position에 대응하는 def_* 값
```

뒷면 Fielding Positions 규칙:

- 레이팅 없는 포지션: 회색 비활성
- 레이팅 있는 포지션: 남색
- 주 포지션: 주황색 강조
- 다이아몬드 그래픽: 실제 레이팅이 있는 포지션만 생성
- 주 포지션 노드: 주황색 배경 + 흰색 텍스트
- 그 외 레이팅 노드: 회색 배경 + 남색 텍스트

## 5. 투수 레이팅

상세 필드:

- `stuff`
- `movement`
- `control`
- `command`
- `stamina`
- `holding`
- `pitchability`
- `pitcher_fielding`
- `velocity_kmh`

현재 앞면 6칸은 다음 순서로 렌더링합니다.

```text
STF = stuff
MOV = movement
CTL = control
CMD = command
STA = stamina
FLD = pitcher_fielding
```

현재 기본 `PLAYER_RATINGS.csv`에는 `holding`, `pitchability`가 없으므로 해당 값은 입력 전까지 `-`로 표시될 수 있습니다.

## 6. Pitch Arsenal

현재 렌더러에서 사용하는 주요 구종:

- `pitch_four_seam`
- `pitch_sinker`
- `pitch_cutter`
- `pitch_slider`
- `pitch_changeup`
- `pitch_curveball`
- `pitch_splitter`
- `pitch_sweeper`
- `pitch_slurve`
- `pitch_knuckleball`

표시 규칙:

- 값 없음: 회색 비활성
- 값 있음: 남색
- 대표 구속에 사용하는 속구 계열 1종(`velocity_pitch`): 주황색
- `velocity_kmh`: 우측 Velocity 원형 영역에 표시

## 7. 선수 투명 PNG

앞면 합성 순서:

```text
front-background.png
→ 선수 투명 PNG
→ front-batter-overlay.png / front-pitcher-overlay.png
→ 동적 텍스트
```

편집기는 선수별로 X / Y / Width / Scale을 조절할 수 있습니다.

현재 브라우저 편집값은 `player_id`별 localStorage에 저장합니다.

향후 CSV 영구 저장용 권장 필드:

- `player_image`
- `player_image_x`
- `player_image_y`
- `player_image_width`
- `player_image_scale`

## 8. 현재 템플릿 소스 오브 트루스

카드 레이아웃/렌더링 수정은 다음 파일만 기준으로 진행합니다.

- `index.html`
- `team-yukies-card.css`
- `team-yukies-card.js`
- `data/`
- `assets/`

과거 `templates/`, Python renderer/studio, V2 spec 문서는 Archive이며 신규 구현에 사용하지 않습니다.
