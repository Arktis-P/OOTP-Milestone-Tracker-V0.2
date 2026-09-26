# 팀 윳키즈 Player Trait 기준

## 1. 목적

`PLAYER_RATINGS.csv`의 `trait_1`, `trait_2`, `trait_3`가 서로 같은 의미를 반복하지 않도록 슬롯별 역할과 허용 용어를 정의한다.

Trait는 레이팅을 대신하는 값이 아니라 카드를 보았을 때 선수의 플레이 스타일을 빠르게 읽게 하는 짧은 태그다.

- 가능하면 각 슬롯은 서로 다른 정보를 전달한다.
- `CONFIRMED` 선수는 세 슬롯을 모두 채운다.
- 새 Trait가 필요하면 임의 문자열을 바로 쓰지 말고 먼저 이 문서의 허용 목록에 추가한다.
- `role`, 투타, 주 포지션처럼 다른 컬럼에 이미 명시된 정보는 특별한 이유가 없으면 그대로 반복하지 않는다.

---

## 2. 타자 Trait

### Trait 1 — 타격의 핵심 스타일

타석에서 선수를 가장 먼저 설명하는 접근법·타구 성향을 적는다.

현재 허용 목록:

- `Contact Hitter`
- `Line Drive Hitter`
- `Power Hitter`
- `Patient Hitter`
- `Aggressive Hitter`
- `Pull Hitter`
- `All-Fields Hitter`

### Trait 2 — 2차 공격 / 주루 특성

Trait 1을 보완하는 장타 생산 방식, 스피드, 주루·도루 성향을 적는다.

현재 허용 목록:

- `Gap Hitter`
- `Speed Threat`
- `Power-Speed Threat`
- `Aggressive Baserunner`
- `Smart Baserunner`
- `Opportunistic Stealer`
- `Extra-Base Threat`

### Trait 3 — 수비 / 다재다능 / 전체 운동능력

수비에서의 대표 강점, 포지션 유연성 또는 선수를 규정할 정도로 뚜렷한 전체 운동능력을 적는다.

현재 허용 목록:

- `Range Defender`
- `Strong Arm Defender`
- `Premium Defender`
- `Multi-Position Athlete`
- `Corner Infielder`
- `Outfield General`
- `Catcher Leader`
- `Five-Tool Athlete`

### 현재 예시

| Player | Trait 1 | Trait 2 | Trait 3 |
|---|---|---|---|
| 히메카와 유키 | Line Drive Hitter | Gap Hitter | Corner Infielder |
| 가나하 히비키 | Contact Hitter | Aggressive Baserunner | Multi-Position Athlete |
| 아라라기 카렌 | Aggressive Hitter | Power-Speed Threat | Five-Tool Athlete |

---

## 3. 투수 Trait

### Trait 1 — 투구의 핵심 아키타입

타자를 상대하는 가장 기본적인 방식과 투수 유형을 적는다.

현재 허용 목록:

- `Power Pitcher`
- `Finesse Pitcher`
- `Command Pitcher`
- `Strikeout Pitcher`
- `Pitch-to-Contact Pitcher`

### Trait 2 — 타구 결과 / 구종 운용 성향

유도하는 타구 유형이나 구종 조합에서 가장 특징적인 부분을 적는다.

현재 허용 목록:

- `Groundballer`
- `Flyball Pitcher`
- `Fastball Heavy`
- `Breaking Ball Specialist`
- `Changeup Specialist`
- `Weak-Contact Specialist`
- `Deception Specialist`

### Trait 3 — 운용 / 내구성 / 특수 능력

선발·불펜에서의 활용 방식, 내구성, 투수 수비나 경기 운영에서 특별히 두드러지는 성질을 적는다.

현재 허용 목록:

- `Workhorse Starter`
- `Durable Starter`
- `Swingman`
- `Multi-Inning Reliever`
- `High-Leverage Reliever`
- `Setup Man`
- `Closer`
- `Fielding Pitcher`
- `Quick Worker`

`role` 컬럼이 이미 `2선발`, `마무리`, `하이 레버리지 불펜`처럼 구체적인 보직을 설명한다면 Trait 3은 가능하면 그 문구를 그대로 복사하기보다 내구성·운용 방식·특수 능력 중 다른 정보를 우선한다.

---

## 4. 선택 원칙

1. 캐릭터를 야구선수로 해석한 뒤 가장 대표적인 세 가지 성질만 남긴다.
2. 높은 레이팅 순서대로 Trait를 고르는 것이 아니다. 플레이 방식이 우선이다.
3. 같은 뜻의 Trait를 두 슬롯에 중복하지 않는다.
4. `Five-Tool Athlete`처럼 전체적인 선수 유형을 나타내는 Trait는 정말 다섯 도구가 모두 평균 이상일 때만 사용한다.
5. 약점은 Trait로 억지로 표현하지 않는다. 약점은 레이팅과 스카우팅 리포트에서 설명한다.
6. 새로운 캐릭터가 기존 목록으로 설명되지 않을 때만 허용 목록을 확장한다.
