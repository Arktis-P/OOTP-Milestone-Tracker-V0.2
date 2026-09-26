# 팀 윳키즈 Player Trait 기준

## 1. 목적

`PLAYER_RATINGS.csv`의 `trait_1`, `trait_2`, `trait_3`는 선수의 서로 다른 세 가지 정체성을 짧게 보여주는 **고정 슬롯**이다.

Trait는 레이팅의 별칭이 아니며, 각 슬롯은 아래에서 정한 범위 중 **정확히 1개**만 선택한다.

- `CONFIRMED` 선수는 Trait 1/2/3을 모두 채운다.
- 각 슬롯은 자기 범위의 허용 목록에서만 선택한다.
- 한 슬롯에 두 개 이상의 Trait를 합쳐 쓰지 않는다.
- 다른 슬롯의 성질을 끌어와 쓰지 않는다.
- 적합한 표현이 없으면 임의 문자열을 쓰지 말고, 먼저 이 문서의 **해당 슬롯 허용 목록**에 새 Trait를 추가한다.
- `role`, 투타, 주 포지션처럼 다른 컬럼에서 이미 명확히 표현되는 정보는 가능하면 반복하지 않는다.

즉 Trait는 자유 태그 3개가 아니라, 선수 유형별로 정해진 **3개의 enum-like 분류값**으로 취급한다.

---

## 2. 타자 Trait

타자는 다음 세 범위에서 하나씩 선택한다.

| Slot | 담당 범위 | 질문 |
|---|---|---|
| Trait 1 | 타격 방식 / 타석 접근 | 이 타자는 **어떻게 치는가?** |
| Trait 2 | 2차 공격 무기 / 주루 압박 | 타격 외에 공격에서 **무엇으로 추가 가치를 만드는가?** |
| Trait 3 | 수비 / 포지션 / 전체 운동능력 | 수비와 포지션 측면에서 **어떤 선수인가?** |

### Trait 1 — 타격 방식 / 타석 접근

다음 중 **1개만** 사용한다.

- `Contact Hitter` — 컨택과 인플레이 타구 생산이 핵심
- `Line Drive Hitter` — 강한 라인드라이브와 배럴 컨트롤이 핵심
- `Power Hitter` — 홈런/장타 파괴력이 핵심
- `Patient Hitter` — 선구안, 카운트 운영, 기다리는 접근이 핵심
- `Aggressive Hitter` — 초구·좋은 공에 적극적으로 승부
- `Pull Hitter` — 당겨치는 방향성이 뚜렷함
- `All-Fields Hitter` — 전 방향 타격 활용이 뚜렷함

### Trait 2 — 2차 공격 무기 / 주루 압박

다음 중 **1개만** 사용한다.

- `Gap Hitter` — 2루타·3루타형 갭 장타
- `Speed Threat` — 순수 스피드가 공격의 주요 무기
- `Power-Speed Threat` — 장타와 스피드를 함께 제공
- `Aggressive Baserunner` — 적극적인 추가 진루와 압박
- `Smart Baserunner` — 상황 판단과 효율적인 진루
- `Opportunistic Stealer` — 선택적이지만 성공률 높은 도루
- `Extra-Base Threat` — 타구 판단과 스피드로 추가 베이스 생산

### Trait 3 — 수비 / 포지션 / 전체 운동능력

다음 중 **1개만** 사용한다.

- `Range Defender` — 넓은 수비 범위가 대표 강점
- `Strong Arm Defender` — 강한 송구가 대표 강점
- `Premium Defender` — 해당 포지션에서 종합적으로 상급 수비
- `Multi-Position Athlete` — 여러 포지션을 실제 전력으로 소화
- `Corner Infielder` — 1B/3B 코너 내야 운용 가치
- `Outfield General` — 외야 전반의 판단·범위·지휘가 강점
- `Catcher Leader` — 포수 리드, 수비 지휘, 투수진 관리가 핵심
- `Five-Tool Athlete` — 컨택·파워·주력·송구·수비가 모두 평균 이상인 전체 운동능력형

### 현재 예시

| Player | Trait 1 | Trait 2 | Trait 3 |
|---|---|---|---|
| 히메카와 유키 | Line Drive Hitter | Gap Hitter | Corner Infielder |
| 가나하 히비키 | Contact Hitter | Aggressive Baserunner | Multi-Position Athlete |
| 아라라기 카렌 | Aggressive Hitter | Power-Speed Threat | Five-Tool Athlete |
| 타카나시 호시노 | Patient Hitter | Smart Baserunner | Catcher Leader |

---

## 3. 투수 Trait

투수는 다음 세 범위에서 하나씩 선택한다.

| Slot | 담당 범위 | 질문 |
|---|---|---|
| Trait 1 | 기본적인 타자 제압 방식 | 이 투수는 **무엇을 중심으로 승부하는가?** |
| Trait 2 | 타구 결과 / 구종 운용 특징 | 공 자체와 결과에서 **무엇이 가장 특징적인가?** |
| Trait 3 | 운용 / 내구성 / 부가 가치 | 시즌과 경기에서 **어떻게 활용되는가?** |

### Trait 1 — 기본적인 타자 제압 방식

다음 중 **1개만** 사용한다.

- `Power Pitcher` — 구속·구위로 타자를 압박
- `Finesse Pitcher` — 속도 차와 섬세한 배합으로 승부
- `Command Pitcher` — 로케이션과 코스 제어가 핵심
- `Strikeout Pitcher` — 헛스윙과 탈삼진 생산이 핵심
- `Pitch-to-Contact Pitcher` — 빠른 승부와 인플레이 타구 유도가 핵심

### Trait 2 — 타구 결과 / 구종 운용 특징

다음 중 **1개만** 사용한다.

- `Groundballer` — 땅볼 유도가 뚜렷함
- `Flyball Pitcher` — 뜬공 유도가 뚜렷함
- `Fastball Heavy` — 속구 계열 사용 비중이 높음
- `Breaking Ball Specialist` — 슬라이더·커브·스위퍼 등 브레이킹볼이 핵심
- `Changeup Specialist` — 체인지업 계열이 대표 무기
- `Weak-Contact Specialist` — 배럴과 강한 타구 억제가 핵심
- `Deception Specialist` — 릴리스, 폼, 궤적 등 디셉션이 핵심

### Trait 3 — 운용 / 내구성 / 부가 가치

다음 중 **1개만** 사용한다.

- `Workhorse Starter` — 많은 이닝과 꾸준한 선발 소화가 대표 가치
- `Durable Starter` — 시즌 내구성과 안정적인 선발 가동이 강점
- `Swingman` — 선발·불펜을 모두 현실적으로 수행
- `Multi-Inning Reliever` — 불펜에서 여러 이닝을 소화
- `High-Leverage Reliever` — 중요한 상황의 불펜 투입 가치
- `Setup Man` — 후반 셋업 역할에 특화
- `Closer` — 경기 마지막 이닝 마무리에 특화
- `Fielding Pitcher` — 투수 수비가 뚜렷한 강점
- `Quick Worker` — 빠른 템포와 효율적인 경기 진행이 특징

`role`이 `1선발급`, `로테이션 홀더`, `마무리`처럼 보직·등급을 이미 설명하더라도 Trait 3은 가능한 한 **내구성, 구체적 운용 방식, 수비·템포 같은 추가 정보**를 우선한다. 다만 `Closer`처럼 그 역할 자체가 선수 정체성인 경우에는 중복을 허용한다.

### 현재 예시

| Player | Trait 1 | Trait 2 | Trait 3 |
|---|---|---|---|
| 카가 | Command Pitcher | Weak-Contact Specialist | Workhorse Starter |
| 비스마르크 | Power Pitcher | Breaking Ball Specialist | Durable Starter |

---

## 4. 선택 절차

1. 먼저 `role`과 원본 레이팅을 확정한다.
2. Trait 1에서 선수의 **가장 대표적인 기본 플레이 방식** 하나를 고른다.
3. Trait 2에서 Trait 1과 겹치지 않는 **두 번째 공격/투구 특징** 하나를 고른다.
4. Trait 3에서 **수비·포지션 또는 운용 가치** 하나를 고른다.
5. 세 Trait가 서로 같은 말을 반복하지 않는지 확인한다.
6. 높은 레이팅 순서가 아니라 **선수의 플레이 정체성**을 기준으로 선택한다.

### 금지 예

- `Power Hitter / Power Hitter / Strong Arm Defender` — 같은 Trait 중복
- `Contact Hitter / Line Drive Hitter / Catcher Leader` — Contact와 Line Drive를 다른 슬롯에 억지로 분산
- `Power Pitcher / Strikeout Pitcher / Closer`에서 Trait 2에 `Strikeout Pitcher`를 넣는 것 — 슬롯 범위 위반
- `Power + Speed`처럼 허용 목록에 없는 자유 문자열 사용

---

## 5. 확장 원칙

새 캐릭터가 기존 목록으로 설명되지 않을 때만 허용 목록을 확장한다.

새 Trait를 추가할 때는 반드시:

1. 타자/투수 중 어느 쪽인지,
2. Trait 1/2/3 중 어느 슬롯인지,
3. 기존 Trait와 의미가 실질적으로 중복되지 않는지,
4. 최소 두 명 이상의 향후 선수에게 재사용 가능성이 있는지

를 확인한다.

특정 캐릭터 한 명만 설명하기 위한 지나치게 고유한 Trait는 만들지 않는다.
