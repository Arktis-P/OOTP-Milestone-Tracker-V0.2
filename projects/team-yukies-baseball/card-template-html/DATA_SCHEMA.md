# TEAM YUKIES Card Template — Current Data Schema

## 1. Source of Truth

- 통합 선수 작업 가이드: `../PLAYER_GUIDE.md`
- 선수 생성/평가 기준: `../docs/PLAYER_CREATION_GUIDELINES.md`
- 신상정보/체형 기준: `../docs/PLAYER_PROFILE_GUIDELINES.md`
- Trait 기준: `../docs/PLAYER_TRAIT_GUIDELINES.md`
- 등번호 선정 기준: `../docs/PLAYER_NUMBER_GUIDELINES.md`
- CSV 작성/갱신 절차: `../docs/PLAYER_RATINGS_WORKFLOW.md`
- 선수 데이터: `../PLAYER_RATINGS.csv`
- 선수 이미지 배치: `data/player_images.js`

`index.html`은 시작 시 `../PLAYER_RATINGS.csv`를 자동 로드한다.

## 2. 공통 필드

- `player_id`
- `character_name`
- `display_first_name`
- `display_last_name`
- `series`
- `team_id`
- `team_code`
- `team_name`
- `card_type`
- `card_year`
- `card_grade`
- `card_theme`
- `theme_index`
- `overall` — 계산값, 1 단위
- `uniform_number`
- `player_type`
- `bats`
- `throws`
- `arm_slot`
- `primary_position`
- `height_cm`
- `weight_kg`
- `birthday` — `MM-DD`
- `birth_place` — 가능하면 `Locality, Prefecture/Province` 형식. 공식 세부 지역이 없으면 작품 내 생활권과 설정을 근거로 추론하며 그 근거는 `notes`에 남긴다.
- `trait_1`–`trait_3`
- `serial` — 계산값
- `status`
- `notes` — 카드에는 표시하지 않는 내부 비고. 등번호 선정 근거, 출생지 추론 근거, 공식 설정과 추정값의 구분 등 나중에 추적할 판단 근거를 기록한다.

CSV 파서는 헤더명을 기준으로 각 행을 읽으므로 `notes` 같은 비표시 필드를 추가해도 기존 카드 렌더링 필드에는 영향을 주지 않는다.

## 3. 타자 카드

### 뒷면 핵심 8개

```text
contact
power
gap_power
discipline
baserunning
stealing
arm
fielding
```

### 앞면 6개

```text
CON  = contact
POW  = power
GAP  = gap_power
DISC = discipline
SPD  = speed
FLD  = fielding
```

`speed`와 야수 `fielding`은 `../docs/PLAYER_CREATION_GUIDELINES.md` 공식으로 계산한다.

포지션별 수비:
- `def_c`
- `def_1b`
- `def_2b`
- `def_3b`
- `def_ss`
- `def_lf`
- `def_cf`
- `def_rf`

## 4. 투수 카드

뒷면 핵심 8개:

```text
stuff
movement
control
command
stamina
holding
pitchability
fielding
```

별도 표시/프로필 지표:
- `velocity_kmh` — 대표 속구 계열 평균 구속
- `groundball_pct` — 예상 땅볼 비율(GB%), 0–100 사이의 퍼센트 값. 20–80 레이팅이 아니며 OVR 계산에 직접 사용하지 않는다.

`groundball_pct`는 투수의 Movement, 구종 구성, 로케이션과 타구 유도 성향을 요약하는 설명용 지표다. 현재 카드 렌더러에는 아직 표시하지 않지만, 추후 투수 카드의 보조 지표로 추가할 수 있도록 CSV 스키마에 유지한다.

공식 구종:
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

## 5. 계산값

CSV에 저장하지만 직접 평가하지 않는 값:

- `speed`
- 야수 `fielding`
- `overall`
- `serial`

원본 값이 변경되면 모두 공식에 따라 다시 계산한다.

## 6. Serial

```text
{TEAM}{YY}{GRADE}{THEME}{THEME_INDEX}{NUMBER}{POSITION}
```

예:

```text
YK261101325
= YK / 26 / 1 / 1 / 01 / 32 / 5
```

포지션 코드:
- 0 DH
- 1 P/SP/RP/CL
- 2 C
- 3 1B
- 4 2B
- 5 3B
- 6 SS
- 7 LF
- 8 CF
- 9 RF

## 7. 이미지

이미지 파일 경로와 카드상 배치는 `data/player_images.js`에서 관리한다.
