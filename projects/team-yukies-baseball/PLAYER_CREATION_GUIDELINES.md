# 팀 윳키즈 캐릭터 야구선수화 기준

## 1. 문서 목적

이 문서는 애니메이션·게임·만화 등 서브컬처 캐릭터를 **현실 야구선수로 재해석**할 때 사용하는 최상위 평가 기준이다.

목표는 원작의 전투력이나 인기도를 그대로 수치화하는 것이 아니라, 캐릭터의 신체 능력·성격·판단력·기술 성향·반복적으로 확인되는 행동을 조사한 뒤 **현실 야구에서 납득 가능한 선수 유형과 20–80 레이팅**으로 번역하는 것이다.

CSV에 실제로 값을 기록하고 계산값을 갱신하는 절차는 `PLAYER_RATINGS_WORKFLOW.md`를 따른다.

---

## 2. 조사와 해석 원칙

### 2.1 자료 우선순위

1. 공식 프로필·공식 설정
2. 원작에서 반복적으로 확인되는 행동과 능력
3. 공식 애니메이션·게임 등 주요 미디어의 일관된 묘사
4. 공식 자료집·인터뷰
5. 신뢰 가능한 2차 자료
6. 제한적인 추론

단발성 개그 장면, 팬덤 밈, 인기, 주인공 보정만으로 높은 레이팅을 부여하지 않는다.

### 2.2 버전 혼합 금지

동일 캐릭터라도 작품 시점·미디어·각성 전후에 따라 능력이 크게 다를 수 있다. 사용자가 특정 버전을 지정하면 그 버전을 우선하고, 지정하지 않으면 대표적인 본편 버전을 기준으로 한다.

서로 다른 버전의 최고점만 모아 한 선수에게 합치지 않는다.

### 2.3 현실 야구로 변환

초능력·마법·비현실적인 전투력은 그대로 경기에서 사용할 수 있다고 가정하지 않는다.

예:

- 초인적인 근력 → 현실적인 Power / Arm / Velocity의 상한 근거
- 높은 반사신경 → Contact / Fielding 근거
- 정밀한 손기술 → Contact / Command / Arm 정확도 근거
- 전술적 사고 → Discipline / Baserunning / Pitchability 근거
- 높은 체력 → Stamina 근거

### 2.4 불확실성

근거가 약한 능력은 45–55를 기본 중립 범위로 본다. 65 이상은 분명한 근거가 필요하고, 70 이상은 캐릭터를 대표하는 강점이어야 한다.

---

## 3. 20–80 스카우팅 스케일

원본 세부 레이팅은 **20–80, 5 단위**로 결정한다.

| Grade | 의미 |
|---:|---|
| 20 | 극단적인 약점 |
| 30 | 매우 낮음 |
| 40 | 평균 이하 |
| 45 | 약간 평균 이하 |
| 50 | MLB 평균 수준 |
| 55 | 약간 평균 이상 |
| 60 | 확실한 Plus |
| 65 | 매우 우수 |
| 70 | 엘리트 / Plus-Plus |
| 75 | 리그 최상위권 |
| 80 | 세대급 최상위 |

다음 계산값은 예외적으로 **1 단위 정수**를 사용한다.

- `speed`
- 야수 `fielding`
- `overall`

---

## 4. 선수 유형과 포지션 결정

사용자가 포지션·역할·선수 유형을 지정하면 우선 적용한다.

예:

- 장타형 3루수
- 컨택 중심 2루수
- 공수겸장 유격수
- 강속구 선발
- 제구형 선발
- 파워 불펜
- 마무리

다만 지정 포지션을 유지하려면 다수의 레이팅을 근거 없이 올려야 하는 경우, 지정안을 유지한 결과와 더 자연스러운 대체 포지션을 함께 보고한다.

포지션별 핵심 특성:

| Position | 특히 중요한 요소 |
|---|---|
| C | Fielding, Arm, 판단력, 리드 |
| 1B | Power, Contact, 기본 포구 |
| 2B | Contact, Fielding, Baserunning |
| 3B | Power, Contact, Arm |
| SS | Fielding, Arm, Contact |
| LF | Power, Contact |
| CF | Fielding, Baserunning, Contact |
| RF | Power, Arm, Contact |
| SP | Stuff, Command, Stamina, Pitchability |
| RP/CL | Stuff, Movement, Command |

---

## 5. 타자 원본 레이팅

다음 항목은 캐릭터 해석을 통해 직접 결정하는 **5 단위 원본 레이팅**이다.

### Contact — `contact`
공을 지속적으로 맞히고 안타성 타구를 만드는 능력.

주요 근거:
- 반응속도
- 손-눈 협응
- 정밀한 동작
- 반복 수행 안정성
- 집중력

### Power — `power`
홈런과 강한 타구를 생산하는 능력.

주요 근거:
- 순수 근력
- 폭발력
- 체격
- 공격적인 성향
- 강한 동작을 반복하는 능력

### Gap Power — `gap_power`
2루타·3루타가 되는 강한 갭 타구를 생산하는 능력. 홈런 Power와 별도로 본다.

### Discipline — `discipline`
볼/스트라이크 판단, 참을성, 패턴 인식, 카운트별 접근.

### Baserunning — `baserunning`
타구 판단, 추가 진루, 상황 판단, 베이스 위에서의 센스.

### Stealing — `stealing`
스타트, 투수 동작 읽기, 도루 타이밍, 도루 성공 능력.

### Arm — `arm`
송구 강도와 정확성의 기본 도구.

### 포지션별 수비 — `def_*`

- `def_c`
- `def_1b`
- `def_2b`
- `def_3b`
- `def_ss`
- `def_lf`
- `def_cf`
- `def_rf`

각 값은 해당 위치에서의 포구·반응·범위·숙련도를 종합한 수비 등급이다.
주 포지션 값은 필수이며 소화하지 않는 포지션은 빈 값으로 둔다.

---

## 6. 타자 계산값

### 6.1 Speed — `speed`

Speed는 단순 평균이 아니라 **실전 주루 판단을 더 넓게 반영하기 위해 Baserunning에 더 큰 비중**을 둔다.

```text
speed = round(
  baserunning × 0.60
+ stealing    × 0.40
)
```

이유:
- Baserunning은 모든 출루·타구 상황에서 반복적으로 작용한다.
- Stealing은 속도와 스타트를 강하게 반영하지만 발생 상황이 더 제한적이다.

### 6.2 Fielding — `fielding`

Fielding은 **주 포지션 수비 등급 + Arm**의 가중합이다.
Arm의 중요도가 포지션별로 다르므로 동일한 50:50 평균을 사용하지 않는다.

| Primary Position | 주 포지션 수비 | Arm |
|---|---:|---:|
| C | 60% | 40% |
| 1B | 90% | 10% |
| 2B | 80% | 20% |
| 3B | 65% | 35% |
| SS | 70% | 30% |
| LF | 85% | 15% |
| CF | 85% | 15% |
| RF | 65% | 35% |

예: 3B

```text
fielding = round(
  def_3b × 0.65
+ arm    × 0.35
)
```

DH는 수비 요약값을 계산하지 않으며 `fielding`은 빈 값으로 둔다.

### 6.3 앞면 타자 6개 요약

```text
CON  = contact
POW  = power
GAP  = gap_power
DISC = discipline
SPD  = speed
FLD  = fielding
```

---

## 7. 타자 Overall 계산

OVR은 카드 뒷면의 핵심 8개 레이팅을 기반으로 계산한다.

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

원본 레이팅은 5 단위지만 **OVR은 가중합 후 가장 가까운 1 단위 정수로 반올림**한다.

포지션별 역할 차이를 반영하기 위해 가중치를 다르게 한다. 각 행의 합은 100%다.

| Pos | CON | POW | GAP | DISC | BR | STL | ARM | FLD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C  | 16 | 16 | 8 | 15 | 4 | 2 | 14 | 25 |
| 1B | 18 | 26 | 12 | 19 | 6 | 2 | 4 | 13 |
| 2B | 20 | 14 | 10 | 18 | 9 | 5 | 7 | 17 |
| 3B | 20 | 25 | 12 | 18 | 3 | 2 | 8 | 12 |
| SS | 18 | 12 | 8 | 16 | 8 | 5 | 10 | 23 |
| LF | 18 | 25 | 12 | 19 | 7 | 3 | 5 | 11 |
| CF | 18 | 14 | 10 | 16 | 10 | 6 | 7 | 19 |
| RF | 18 | 24 | 12 | 18 | 5 | 2 | 10 | 11 |
| DH | 22 | 28 | 14 | 22 | 8 | 6 | 0 | 0 |

계산 예:

```text
3B OVR =
  contact     × 0.20
+ power       × 0.25
+ gap_power   × 0.12
+ discipline  × 0.18
+ baserunning × 0.03
+ stealing    × 0.02
+ arm         × 0.08
+ fielding    × 0.12
```

최종값은 20–80 범위로 제한한다.

---

## 8. 투수 원본 레이팅

투수의 뒷면 핵심 레이팅은 다음 8개다. 모두 20–80, 5 단위 원본값이다.

### Stuff — `stuff`
헛스윙과 타자 제압 능력.

### Movement — `movement`
배럴 회피, 공의 움직임, 강한 타구 억제.

### Control — `control`
스트라이크를 안정적으로 던지고 볼넷을 억제하는 능력.

### Command — `command`
원하는 코스와 높이에 공을 배치하는 능력.

### Stamina — `stamina`
구위와 투구 동작을 오래 유지하는 능력.

### Holding — `holding`
주자 견제, 투구 동작 관리, 도루 억제 능력.

### Pitchability — `pitchability`
구종 배합, 타자 상대 계획, 카운트 운영, 경기 중 조정 능력.

### Fielding — `fielding`
번트·투수 앞 땅볼·베이스 커버 등 투수 수비.

### Velocity — `velocity_kmh`

20–80 레이팅이 아니라 **대표적으로 사용하는 속구 계열 구종의 평균 구속(km/h)**이다.

Velocity는 Stuff의 근거 중 하나이므로 OVR에 다시 직접 넣지 않는다.

---

## 9. 투수 구종

현재 공식 구종은 다음 10개만 사용한다.

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

각 구종은 종합 품질을 20–80, 5 단위로 평가한다.
사용하지 않는 구종은 빈 값으로 둔다.

개별 구종 구속은 별도로 저장하지 않는다.

---

## 10. 투수 Overall 계산

OVR은 뒷면의 8개 핵심 레이팅만 사용한다.

### SP

```text
overall = round(
  stuff        × 0.20
+ movement     × 0.15
+ control      × 0.14
+ command      × 0.16
+ stamina      × 0.15
+ holding      × 0.05
+ pitchability × 0.10
+ fielding     × 0.05
)
```

### RP / CL

```text
overall = round(
  stuff        × 0.27
+ movement     × 0.17
+ control      × 0.14
+ command      × 0.17
+ stamina      × 0.05
+ holding      × 0.05
+ pitchability × 0.10
+ fielding     × 0.05
)
```

Velocity와 개별 구종 등급은 Stuff·Movement·Pitchability를 결정하는 근거이므로 OVR에 직접 중복 가중하지 않는다.

OVR 계산에 필요한 8개 값 중 하나라도 없으면 OVR을 확정하지 않는다.

---

## 11. 카드 메타데이터와 Serial Number

시리얼은 사람이 직접 조합하지 않고 다음 필드로 계산한다.

```text
{TEAM}{YY}{GRADE}{THEME}{THEME_INDEX}{NUMBER}{POSITION}
```

규칙:

- `team_code`: 2자리 팀 코드. 팀 윳키즈 = `YK`
- `card_year`: 연도 뒤 2자리. 2026 = `26`
- `card_grade`: 1자리. 현재 Common = `1`; 높은 등급일수록 더 높은 숫자
- `card_theme`: 1자리 테마 코드. 현재 첫 테마 = `1`
- `theme_index`: 같은 테마 안에서의 카드 순서. `01`–`99`
- `uniform_number`: `00`–`99`
- `primary_position`: 아래 포지션 코드로 변환

| Code | Position |
|---:|---|
| 0 | DH |
| 1 | P / SP / RP / CL |
| 2 | C |
| 3 | 1B |
| 4 | 2B |
| 5 | 3B |
| 6 | SS |
| 7 | LF |
| 8 | CF |
| 9 | RF |

예: Yukies / 2026 / Grade 1 / Theme 1 / Theme #01 / #32 / 3B

```text
YK + 26 + 1 + 1 + 01 + 32 + 5
= YK261101325
```

`theme_index`는 같은 `team_code + card_year + card_grade + card_theme` 조합 안에서 중복되지 않아야 한다.
이미 발급한 카드의 `theme_index`는 다른 카드를 삭제해도 재번호를 매기지 않는다.

---

## 12. 선수 생성 순서

1. 캐릭터와 기준 버전을 확정한다.
2. 공식 자료 우선으로 캐릭터 특성을 조사한다.
3. 핵심 특징 3–7개를 추출한다.
4. 포지션·역할·투타를 정한다.
5. 타자 또는 투수의 **원본 레이팅을 5 단위**로 결정한다.
6. 포지션별 수비 또는 실제 사용하는 구종을 결정한다.
7. 계산값 `speed`, 야수 `fielding`, `overall`을 계산한다.
8. 카드 메타데이터와 `theme_index`를 정한다.
9. `serial`을 계산한다.
10. 스카우팅 리포트를 작성한다.
11. `PLAYER_RATINGS_WORKFLOW.md`에 따라 CSV를 갱신·검증한다.

---

## 13. 인플레이션 방지

- 50은 MLB 평균 수준이다.
- 65+는 명백한 강점이어야 한다.
- 70+는 캐릭터를 대표하는 특징이어야 한다.
- 75+는 극소수에게만 허용한다.
- 80은 세대급 최상위 능력에만 사용한다.
- 모든 캐릭터를 스타로 만들지 않는다.
- 약점이 없는 선수는 매우 드물어야 한다.
- 원작에서 강하다는 이유만으로 모든 운동 능력을 높이지 않는다.

---

## 14. 최종 결과의 목표

좋은 결과는 단순히 높은 OVR의 선수가 아니다.

원작을 아는 사람이 프로필을 보았을 때 다음과 같은 인상을 받을 수 있어야 한다.

> "이 캐릭터가 현실에서 야구선수가 되었다면 정말 이런 유형이었을 것 같다."

캐릭터 해석의 설득력, 현실 야구에서의 역할 적합성, 전체 선수군에 대한 동일한 20–80 기준을 우선한다.
