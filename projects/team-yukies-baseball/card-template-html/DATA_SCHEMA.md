# TEAM YUKIES Card Template — Current Data Schema

선수 데이터의 단일 원본은 `../PLAYER_RATINGS.csv`입니다.
선수 생성·평가·계산 규칙의 최상위 기준 문서는 프로젝트 루트의 `PLAYER_CREATION_GUIDELINES.md`입니다.

## 1. 로딩 규칙

- `index.html` → `team-yukies-card.js`
- 시작 시 `../PLAYER_RATINGS.csv` 자동 로드
- `card-template-html/data/`에는 별도 선수 레이팅 CSV를 두지 않음
- 상단 CSV 파일 선택은 임시/수동 확인용

## 2. 공통/카드 메타데이터

- `player_id`
- `character_name`
- `display_first_name`
- `display_last_name`
- `series`
- `team_id`
- `team_code` — 팀 윳키즈는 `YK`
- `team_name`
- `card_type`
- `card_year` — 발행 연도 뒤 2자리
- `card_grade` — 현재 Common = 1
- `card_theme` — 테마 번호
- `overall` — 계산값
- `uniform_number`
- `player_type`
- `primary_position`
- `serial` — 계산값
- `status`

## 3. 신상 정보

- `height_cm`
- `weight_kg`
- `bats`
- `throws`
- `birthday` — `MM-DD`
- `birth_place`
- `trait_1`
- `trait_2`
- `trait_3`

## 4. 타자

원본 레이팅:
- `contact`
- `power`
- `gap_power`
- `discipline`
- `baserunning`
- `stealing`
- `arm`
- `def_c`, `def_1b`, `def_2b`, `def_3b`, `def_ss`, `def_lf`, `def_cf`, `def_rf`

계산값:
- `speed = round((baserunning + stealing) / 2)`
- `fielding = round((arm + primary_position_fielding) / 2)`
- `overall`
- `serial`

앞면 6칸:
```text
CON / POW / GAP / DISC / SPD / FLD
```

## 5. 투수

- `stuff`
- `movement`
- `control`
- `command`
- `stamina`
- `holding`
- `pitchability`
- `fielding`
- `velocity_kmh`

`velocity_kmh`는 대표 속구 계열 구종의 평균 구속이다. `velocity_pitch`는 사용하지 않는다.

## 6. 공식 구종 10종

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

그 외 구종 컬럼은 현재 스키마에서 사용하지 않는다.

## 7. 재계산 규칙

다음은 CSV에 값을 저장하지만 독립 입력값이 아니다.

- `speed`
- 야수 `fielding`
- `overall`
- `serial`

관련 원본 값 또는 선수 정보가 수정될 때마다 `PLAYER_CREATION_GUIDELINES.md`의 공식에 따라 다시 계산해 CSV에 기록한다. 렌더러도 같은 공식을 다시 적용하여 오래된 계산값을 화면에 사용하지 않는다.

## 8. 이미지 데이터

이미지 경로와 배치는 `data/player_images.js`에서 별도 관리한다.

- `image_src`
- `x`
- `y`
- `width`
- `scale`
