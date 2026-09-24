# TEAM YUKIES Card Template — Current Data Schema

현재 HTML/CSS/JS 카드 템플릿의 선수 데이터 원본은 **`../PLAYER_RATINGS.csv` 하나**입니다.

## 1. 로딩 규칙

- `index.html` → `team-yukies-card.js`
- 시작 시 `../PLAYER_RATINGS.csv` 자동 로드
- `card-template-html/data/`에는 별도 레이팅 CSV를 두지 않음
- `file://` 직접 실행은 브라우저 정책으로 CSV fetch가 막힐 수 있으므로 로컬 HTTP 서버 실행을 기준으로 함
- 상단 CSV 파일 선택은 임시/수동 데이터 확인용

## 2. 공통 카드 필드

- `player_id`
- `character_name`
- `display_first_name`
- `display_last_name`
- `series`
- `team_id`
- `team_name`
- `card_type`
- `overall`
- `uniform_number`
- `player_type`: `BATTER` / `PITCHER`
- `primary_position`
- `scouting_report`
- `serial`
- `status`

## 3. 신상 정보

뒷면 상단 프로필 3줄에 다음 필드를 사용합니다.

- `height_cm`
- `weight_kg`
- `bats`
- `throws`
- `birthday`
- `birth_place`
- `trait_1`
- `trait_2`
- `trait_3`

출력 구조:

```text
{height_cm}cm | {weight_kg}kg | Bats: {bats} | Throws: {throws}
{birthday} | {birth_place}
{trait_1} | {trait_2} | {trait_3}
```

## 4. 타자 레이팅

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

앞면 6칸:

```text
CON = contact
POW = power
GAP = gap
EYE = eye
SPD = baserunning
FLD = primary_position에 대응하는 def_* 값
```

## 5. 투수 레이팅

- `stuff`
- `movement`
- `control`
- `command`
- `stamina`
- `holding`
- `pitchability`
- `pitcher_fielding`
- `velocity_kmh`
- `velocity_pitch`

앞면 6칸:

```text
STF = stuff
MOV = movement
CTL = control
CMD = command
STA = stamina
FLD = pitcher_fielding
```

뒷면은 위 8개 레이팅 중 `velocity_kmh`와 `velocity_pitch`를 제외한 8개 항목을 사용합니다. 값이 비어 있으면 `-`로 표시합니다.

## 6. Pitch Arsenal

CSV에는 다음 구종 컬럼을 유지합니다.

- `pitch_four_seam`
- `pitch_sinker`
- `pitch_cutter`
- `pitch_slider`
- `pitch_sweeper`
- `pitch_slurve`
- `pitch_curveball`
- `pitch_knuckle_curve`
- `pitch_slow_curve`
- `pitch_changeup`
- `pitch_splitter`
- `pitch_forkball`
- `pitch_screwball`
- `pitch_knuckleball`

현재 카드 Pitch Arsenal 영역은 주요 10종을 표시하며, `velocity_pitch`와 일치하는 표시 구종을 강조합니다.

## 7. 선수 이미지

이미지 파일 경로와 배치는 `PLAYER_RATINGS.csv`가 아니라 `data/player_images.js`에서 관리합니다.

- `image_src`
- `x`
- `y`
- `width`
- `scale`

세부 규칙은 `PLAYER_IMAGE_DATA.md`를 따릅니다.

## 8. 현재 소스 오브 트루스

레이팅/프로필:
- `../PLAYER_RATINGS.csv`

이미지 경로/배치:
- `data/player_images.js`

레이아웃/렌더링:
- `index.html`
- `team-yukies-card.css`
- `team-yukies-card.js`
- `assets/`
- `fonts/`

과거 `templates/`, Python renderer/studio, V2 spec 문서는 Archive이며 신규 구현에 사용하지 않습니다.
