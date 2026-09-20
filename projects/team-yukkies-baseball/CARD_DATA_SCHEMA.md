# Team Yukkies Card Data Schema

## 1. 목적

`PLAYER_RATINGS.csv`는 선수 생성 결과와 카드 렌더링에 필요한 데이터를 하나의 행으로 관리한다.

사용자 피로를 줄이기 위해 **같은 정보를 두 번 입력하지 않는 것**을 원칙으로 한다. 카드에 필요한 값 중 계산 가능한 값은 CSV에 중복 저장하지 않고 렌더러에서 파생한다.

---

## 2. 공통 식별 정보

- `player_id`: 선수 고유 ID. 파일명 기준에도 사용한다.
- `character_name`: 카드에 표시할 선수 이름.
- `series`: 원작/시리즈 식별용.
- `team_id`: 팀 고유 ID.
- `team_name`: 카드에 표시할 팀명.
- `card_type`: 기본값 `BASE`. 추후 ALL_STAR, GOLD_GLOVE 등 특수 카드에 사용.
- `overall`: 20–80 종합 능력치. 1 단위 정수.
- `uniform_number`: 등번호.
- `player_type`: `BATTER`, `PITCHER`, 필요 시 추후 `TWO_WAY`.
- `bats`: RIGHT / LEFT / SWITCH.
- `throws`: RIGHT / LEFT.
- `arm_slot`: 투수 전용. OVERHAND / THREE_QUARTER / SIDEARM / UNDERHAND.
- `primary_position`: 야수는 C/1B/2B/3B/SS/LF/CF/RF, 투수는 SP/RP/CL.

### 에셋 파일 규칙

이미지 경로를 CSV에 매번 입력하지 않는다.

- 선수 이미지: `assets/players/{player_id}.png`
- 팀 로고: `assets/teams/{team_id}.png`

필요한 파일만 해당 위치에 넣으면 렌더러가 자동으로 찾는다.

---

## 3. 타자 상세 능력치

20–80, 기본적으로 5 단위 평가.

- `contact`: 컨택.
- `power`: 홈런/강한 장타 파워.
- `gap`: 2루타·3루타 등 갭 장타 생산 능력.
- `eye`: 선구안과 타석 판단.
- `baserunning`: 타구 판단, 추가 진루 등 주루 센스.
- `stealing`: 스타트, 도루 성공 가능성 등 도루 능력.
- `arm`: 야수의 기본 송구 능력.

### BASE 카드 앞면 타자 6개 요약

레퍼런스 카드의 한 줄 스탯 스트립에 맞춰 다음 6개를 표시한다.

- CON = `contact`
- POW = `power`
- GAP = `gap`
- EYE = `eye`
- SPD = round((`baserunning` + `stealing`) / 2)
- FLD = 주 포지션에 대응하는 `def_*` 값

`baserunning`, `stealing`, `arm` 원본 값은 뒷면 상세 정보와 OVR 계산에 유지한다.
SPD는 순수 100m 달리기 속도가 아니라 **실전 주자 능력 요약값**으로 정의한다.

---

## 4. 포지션별 수비

야수 수비는 하나의 공통 Fielding 값으로 저장하지 않는다.

- `def_c`
- `def_1b`
- `def_2b`
- `def_3b`
- `def_ss`
- `def_lf`
- `def_cf`
- `def_rf`

각 값은 해당 포지션에서의 **종합 수비 능력**을 뜻한다. 포구, 반응, 범위, 송구, 포지션 숙련도를 모두 포함한다.

규칙:

- `primary_position`에 대응하는 수비값은 필수.
- 다른 `def_*` 값이 있으면 자동으로 부포지션으로 간주.
- 빈 칸은 해당 포지션을 실전 수비 위치로 사용하지 않는다는 뜻.
- 별도의 `secondary_positions` 컬럼은 두지 않는다.

카드 뒷면의 수비 다이아몬드는 이 값들만 읽어서 자동 생성한다.

---

## 5. 투수 상세 능력치

20–80, 기본적으로 5 단위 평가.

- `stuff`: 헛스윙과 타자 제압 능력.
- `movement`: 공의 움직임과 강한 타구 억제 능력.
- `control`: 스트라이크를 안정적으로 던지는 능력.
- `command`: 원하는 위치에 공을 배치하는 능력.
- `stamina`: 긴 이닝 동안 투구 능력을 유지하는 능력.
- `pitcher_fielding`: 투수 수비.
- `velocity_kmh`: 속구 계열의 대표 평균 구속. 20–80이 아닌 실제 km/h.

### BASE 카드 앞면 투수 6개 요약

- STF = `stuff`
- MOV = `movement`
- CTL = `control`
- CMD = `command`
- STA = `stamina`
- VEL = `velocity_kmh` (실제 km/h)

`pitcher_fielding`은 뒷면 Detailed Ratings에서 표시한다.
대표 구속은 앞면에서 빠르게 읽히도록 VEL 슬롯에 표시하고, 뒷면 Fastball Velocity 배너에서도 크게 반복한다.

---

## 6. 투수 구종

Statcast의 현행 고유 구종 분류를 기준으로 미리 열을 둔다.

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

각 값은 해당 구종의 **종합 품질 20–80 등급**이다.

구종별 개별 구속은 저장하지 않는다. 카드에는 선수의 대표 속구 평균 구속 `velocity_kmh`만 별도로 표시한다.

빈 구종 컬럼은 해당 구종을 사용하지 않는다는 뜻이다.

---

## 7. OVR 계산식 v1

OVR은 20–80 범위의 정수지만 상세 능력치와 달리 **1 단위**로 표시한다.

최종값은 가장 가까운 정수로 반올림하고 20–80으로 제한한다.

### 7.1 타자

먼저 공격력 `BAT`를 계산한다.

```text
BAT =
  Contact × 0.30
+ Power   × 0.30
+ Gap     × 0.15
+ Eye     × 0.25
```

주자 요약값:

```text
SPD = (Baserunning + Stealing) / 2
```

주 포지션에 따라 OVR 가중치를 다르게 한다.

| 주 포지션 | 계산 |
|---|---|
| C | BAT × 0.72 + FLD × 0.23 + SPD × 0.05 |
| 1B / LF / RF | BAT × 0.88 + FLD × 0.07 + SPD × 0.05 |
| 2B / 3B | BAT × 0.85 + FLD × 0.10 + SPD × 0.05 |
| SS / CF | BAT × 0.75 + FLD × 0.20 + SPD × 0.05 |

수비 부담이 큰 포지션일수록 FLD 비중을 높인다.

`arm`은 각 포지션의 종합 `def_*` 값에 이미 반영되므로 OVR에서 다시 더하지 않는다.

### 히메카와 유키 예시

```text
BAT = 60×0.30 + 70×0.30 + 60×0.15 + 55×0.25
    = 61.75

SPD = (50 + 50) / 2
    = 50

3B OVR = 61.75×0.85 + 50×0.10 + 50×0.05
       = 59.9875
       → 60
```

### 7.2 투수

선발:

```text
SP OVR =
  Stuff            × 0.30
+ Movement         × 0.20
+ Control          × 0.18
+ Command          × 0.17
+ Stamina          × 0.12
+ Pitcher Fielding × 0.03
```

불펜/마무리:

```text
RP/CL OVR =
  Stuff            × 0.38
+ Movement         × 0.22
+ Control          × 0.18
+ Command          × 0.17
+ Stamina          × 0.02
+ Pitcher Fielding × 0.03
```

`velocity_kmh`와 개별 구종 등급은 OVR에 직접 다시 넣지 않는다.

이 정보는 이미 Stuff와 투수 프로필을 정할 때 중요한 근거가 되므로 직접 가중하면 같은 장점을 이중 계산할 가능성이 높다.

---

## 8. 카드 뒷면 자동 표시 규칙

### 타자

1. 선수 정보 요약.
2. Contact / Power / Gap / Eye / Baserunning / Stealing / Arm의 20–80 막대.
3. 야구장 다이아몬드 위에 값이 존재하는 `def_*` 위치만 표시.
4. 각 포지션 마커에 수비 등급 표시.
5. `scouting_report`.

### 투수

1. 선수 정보 요약 및 arm slot.
2. Stuff / Movement / Control / Command / Stamina / Pitcher Fielding의 20–80 막대.
3. `velocity_kmh`를 실제 km/h로 크게 표시.
4. 값이 존재하는 `pitch_*` 구종과 20–80 등급만 표시.
5. `scouting_report`.

---

## 9. 자동 렌더링 시 원칙

사용자가 카드 한 장을 만들기 위해 직접 디자인 툴을 만질 필요가 없도록 한다.

최종 렌더러는 다음 세 가지만 있으면 카드를 만들 수 있어야 한다.

1. `PLAYER_RATINGS.csv`의 선수 행.
2. `assets/players/{player_id}.png` 선수 이미지.
3. `assets/teams/{team_id}.png` 팀 로고.

권장 구현은 **고정 SVG/HTML 템플릿 + 코드 기반 렌더러**다. Figma는 필수가 아니며 사용자가 직접 수정해야 하는 작업 흐름에 포함하지 않는다.

템플릿은 타자 앞/뒤, 투수 앞/뒤 4종만 유지하고 CSV 값과 에셋을 자동 배치한다.
