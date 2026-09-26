# PLAYER_RATINGS.csv 갱신 워크플로

## 1. 목적

이 문서는 `PLAYER_CREATION_GUIDELINES.md`에 따라 결정한 선수 데이터를 `PLAYER_RATINGS.csv`에 기록하고, 파생값을 재계산하고, 카드 템플릿에서 사용할 수 있는 상태로 검증하는 절차를 정의한다.

- 평가 기준: `PLAYER_CREATION_GUIDELINES.md`
- Trait 기준: `PLAYER_TRAIT_GUIDELINES.md`
- 단일 데이터 원본: `PLAYER_RATINGS.csv`
- 카드 표시 스키마: `card-template-html/DATA_SCHEMA.md`

---

## 2. 직접 입력값과 계산값

### 직접 입력 / 조사값

공통:
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
- `uniform_number`
- `player_type`
- `bats`
- `throws`
- `arm_slot`
- `primary_position`
- `height_cm`
- `weight_kg`
- `birthday`
- `birth_place`
- `trait_1`–`trait_3`
- `reference_player`
- `role`
- `scouting_report`
- `status`

타자 원본 레이팅:
- `contact`
- `power`
- `gap_power`
- `discipline`
- `baserunning`
- `stealing`
- `arm`
- `def_c`–`def_rf`

투수 원본 레이팅:
- `stuff`
- `movement`
- `control`
- `command`
- `stamina`
- `holding`
- `pitchability`
- `fielding`
- `velocity_kmh`
- 공식 구종 10종

### 계산값

- `speed` — 타자만
- `fielding` — 야수는 계산값, 투수는 직접 평가값
- `overall`
- `serial`

계산값은 수동 밸런스 조정용 값이 아니다. 원본 데이터가 바뀌면 반드시 공식에 따라 다시 계산한다.

---

## 3. 신규 선수 추가 절차

### Step 1. 식별 정보

`player_id`는 영문 소문자 snake_case로 고유하게 만든다.

예:

```text
himekawa_yuki
ganaha_hibiki
```

### Step 2. 기본 프로필

생일은 연도 없이 `MM-DD`로 저장한다.

```text
09-14
10-10
```

투타·주 포지션·등번호·신체정보를 확정한다.

공식 신상정보가 없는 경우에는 확인되지 않은 값을 공식 설정처럼 단정하지 않는다. 야구선수화에 필요한 추정값을 넣을 수는 있지만, 캐릭터의 체형·운동능력과 현실적인 선수 체격을 근거로 보수적으로 결정한다.

### Step 3. Trait 입력

`PLAYER_TRAIT_GUIDELINES.md`를 따라 `trait_1`, `trait_2`, `trait_3`을 슬롯별 의미에 맞게 입력한다.

- Trait 1: 핵심 플레이 스타일
- Trait 2: 2차 성향 / 결과 유형
- Trait 3: 수비·다재다능·운용 등 보조 정체성

CONFIRMED 선수는 세 Trait을 모두 채우며, 새로운 Trait이 필요하면 먼저 Trait 기준 문서의 허용 목록을 갱신한다.

### Step 4. 원본 레이팅 입력

`PLAYER_CREATION_GUIDELINES.md`를 기준으로 **20–80, 5 단위**로 결정한다.

CONFIRMED 선수는 OVR 계산에 필요한 핵심 뒷면 레이팅이 모두 채워져 있어야 한다.

### Step 5. 타자 파생값

```text
speed = round(baserunning × 0.60 + stealing × 0.40)
```

`fielding`은 주 포지션별 수비/Arm 가중치를 적용한다.

예: 3B

```text
fielding = round(def_3b × 0.65 + arm × 0.35)
```

### Step 6. Overall

타자:
- 뒷면의 `contact, power, gap_power, discipline, baserunning, stealing, arm, fielding`
- 주 포지션별 가중치 적용

투수:
- 뒷면의 `stuff, movement, control, command, stamina, holding, pitchability, fielding`
- SP 또는 RP/CL 가중치 적용

최종값은 20–80 범위의 **1 단위 정수**다.

### Step 7. 카드 메타데이터와 theme_index

현재 기본값:

```text
team_code   = YK
card_year   = 26
card_grade  = 1
card_theme  = 1
```

`theme_index`는 같은 `team_code + card_year + card_grade + card_theme` 안에서 다음 미사용 번호를 사용한다.

- 첫 카드 = 01
- 두 번째 카드 = 02
- ...
- 최대 = 99

**실제로 확정·발급된 카드의 번호는 삭제 후에도 재사용하지 않는다.** 반면 잘못 추가된 임시 행, 테스트 데이터, 발급 전에 폐기된 DRAFT처럼 실제 카드로 존재한 적이 없는 데이터는 번호를 소비한 것으로 보지 않는다. 이런 오류 데이터를 제거한 뒤에는 연속된 다음 번호를 다시 사용한다.

### Step 8. Serial 계산

```text
serial =
  TEAM
+ YY
+ GRADE(1)
+ THEME(1)
+ THEME_INDEX(2)
+ UNIFORM_NUMBER(2)
+ POSITION(1)
```

예:

```text
YK + 26 + 1 + 1 + 01 + 32 + 5
= YK261101325
```

### Step 9. CSV 행 저장

CSV 헤더 순서를 바꾸지 않고 해당 선수 행을 추가한다.

빈 값:
- 사용하지 않는 야수 포지션
- 사용하지 않는 구종
- 타자에게 해당하지 않는 투수 능력
- 투수에게 해당하지 않는 타자 능력

은 빈 셀로 유지한다.

---

## 4. 기존 선수 수정 절차

선수의 원본 정보 하나라도 변경되면 관련 계산값을 다시 확인한다.

| 변경 항목 | 재계산 |
|---|---|
| `baserunning`, `stealing` | `speed`, `overall` |
| `arm`, 주 포지션 `def_*`, `primary_position` | 야수 `fielding`, `overall`, 필요 시 `serial` |
| 타자 뒷면 8개 값 | `overall` |
| 투수 뒷면 8개 값 | `overall` |
| `team_code`, `card_year`, `card_grade`, `card_theme`, `theme_index`, `uniform_number`, `primary_position` | `serial` |
| 등번호 | `serial` |
| 포지션 | `fielding`, `overall`, `serial` |

`overall`이나 `serial`을 기존 값 그대로 둔 채 원본만 수정해서는 안 된다.

---

## 5. 검증 규칙

CONFIRMED 상태로 두기 전에 다음을 확인한다.

### 공통

- `player_id` 중복 없음
- `birthday` = `MM-DD`
- `uniform_number` = 0–99
- `card_grade` = 한 자리
- `card_theme` = 한 자리
- `theme_index` = 1–99, 같은 테마 범위에서 중복 없음
- `serial`이 공식 결과와 일치
- `trait_1`–`trait_3`이 모두 존재하고 `PLAYER_TRAIT_GUIDELINES.md`의 슬롯 의미와 허용 목록을 따름

### 타자

- 핵심 원본 레이팅은 20–80, 5 단위
- 주 포지션 `def_*` 존재
- `speed`, `fielding`, `overall` 재계산 완료

### 투수

- 8개 뒷면 핵심 레이팅 존재
- `velocity_kmh` 존재
- 사용하는 구종만 값 존재
- `overall` 재계산 완료

---

## 6. 카드 템플릿과의 관계

`card-template-html/index.html`은 프로젝트 루트의 `PLAYER_RATINGS.csv`를 읽는다.

렌더러는 계산값을 다시 계산하여 오래된 CSV 파생값이 화면에 그대로 표시되지 않게 한다. 그러나 저장소의 CSV도 동일한 값을 유지해야 하므로 **CSV 수정 작업 자체에서도 계산값을 반드시 갱신**한다.

이미지 경로와 배치는 별도 파일 `card-template-html/data/player_images.js`에서 관리한다.
