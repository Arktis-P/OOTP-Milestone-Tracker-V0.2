# OOTP Milestone Tracker V0.2 — Rules & Policies

이 문서는 마일스톤, 연속 기록, 예측 등 **기준값 기반 기능의 작성 방식과 판정 원칙**을 정의한다.

목표는 다음과 같다.

- 기준을 코드와 분리한다.
- 정책 key를 안정적으로 유지한다.
- 숫자 조정만으로 기능 로직을 깨지 않게 한다.
- 자동 판정, UI 표시, 예측이 같은 기준을 공유한다.

---

# 1. 정책 데이터의 위치

권장 구조:

```text
data/
├─ milestones.csv
├─ streak_policies.json
└─ bundle_manifest.json
```

정책 데이터는 Git에 포함한다.
사용자가 편집할 수 있게 만들 경우 사용자 override와 bundle 원본을 분리한다.

---

# 2. Milestone Policy Schema

권장 CSV 필드:

```csv
category,key,label,scope,stat,threshold,direction,grade,track_from,near_n,description_template
```

## `category`

예:
- batting
- pitching
- team
- postseason
- award

## `key`

정책의 영구 식별자다.

예:

```text
bat_game_hr_3
bat_season_hr_40
bat_career_hits_3000
pit_season_so_200
team_season_wins_100
```

### key 원칙

- 화면 라벨이 바뀌어도 key는 바꾸지 않는다.
- threshold를 수정해야 하는 경우 기존 사용자의 기록 의미가 변하는지 검토한다.
- 기존 key 삭제보다 deprecated 처리 또는 migration을 우선한다.

## `label`

사용자에게 보여줄 이름.

예:
- 한 경기 3 홈런
- 시즌 40 홈런
- 통산 3000 안타

UI 다국어가 구현되면 label 자체를 번역 key로 대체하거나 별도 localization layer를 둘 수 있다.

## `scope`

허용 예:

```text
game
season
career
team_game
team_season
```

필요 시 `manual` 전용 항목도 확장 가능하지만 자동 계산 여부와 혼동하지 않는다.

## `stat`

판정기가 이해하는 안정적인 stat key.

예:

```text
h
hr
rbi
sb
so
w
sv
hold
season_avg
season_ops
career_hr
cycle
perfect_game
season_hr_sb
```

OOTP 원본 헤더명을 직접 policy key로 쓰지 않는다. parser가 원본 이름을 canonical stat으로 변환한다.

## `threshold`

숫자 또는 복합 조건 표현.

예:

```text
40
.300
3.00
30-30
1
```

복합 조건은 가능한 한 별도 parser/evaluator를 두고 ad-hoc 문자열 비교를 하지 않는다.

## `direction`

권장:

```text
higher
lower
boolean
```

예:
- HR 40: higher
- ERA 3.00 이하: lower
- cycle: boolean

## `grade`

권장 고정값:

```text
common
uncommon
rare
epic
legendary
```

grade는 UI 강조와 필터에 사용한다.
판정 로직 자체를 grade에 의존시키지 않는다.

## `track_from`

예측 목록에 목표를 언제부터 올릴지 결정한다.

통산 누적 기록에서는 **목표까지 남은 값 기준**을 권장한다.

예:
- threshold 3000 hits
- track_from 300
- 현재 2699까지는 숨김
- 현재 2700부터 추적 후보

비율 기록이나 특수 기록에 불필요하면 비운다.

## `near_n`

목표 임박 강조 범위.

예:
- threshold 500 HR
- near_n 5
- 현재 495 이상이면 임박 강조

## `description_template`

이벤트 문구를 만드는 template key.

정책 CSV에 긴 자연어 문장을 반복 저장하기보다 template registry를 통해 관리하는 방식을 권장한다.

---

# 3. 판정 기본 규칙

## 3.1 Counting Stat Crossing

시즌/통산 누적 기록의 기본 규칙:

```text
previous < threshold <= current
```

이벤트는 threshold를 **처음 통과한 시점**에 한 번만 생성한다.

예:

```text
previous HR = 39
current HR = 41
threshold = 40
→ 시즌 40 홈런 달성 생성
```

이미 40 HR 이벤트가 DB에 있으면 재생성하지 않는다.

## 3.2 다단계 threshold

한 경기 기록처럼 동일 stat에 threshold가 여러 개 존재할 수 있다.

예:
- 2 HR
- 3 HR
- 4 HR
- 5+ HR

한 경기 4 HR이면 기본적으로 가장 높은 충족 단계인 `4 HR` 하나를 기록한다.

단, 시즌/통산 누적 crossing은 서로 다른 역사적 milestone이므로 30→40 HR처럼 각 단계가 별도 시점에 기록될 수 있다.

## 3.3 Boolean Event

예:
- cycle
- grand slam
- no-hitter
- perfect game

parser 또는 event detector가 boolean 사실을 제공하면 해당 policy를 생성한다.

같은 game/subject/policy는 unique하게 유지한다.

---

# 4. 시즌 누적 기록

박스스코어 import 후 해당 경기까지의 현재 시즌 값을 계산한다.

예:
- H
- HR
- RBI
- R
- SB
- BB
- W
- SO
- SV
- HLD
- IP

이전 경기까지의 값과 현재 경기 포함 값을 비교해 crossing을 판정한다.

---

# 5. 통산 기록

통산 기록은 baseline과 앱 import 이후 증분을 결합한다.

```text
career_current = baseline_at_anchor + increment_after_anchor
```

중요:

- baseline refresh가 기존 통산값을 또 더하는 구조가 되어서는 안 된다.
- anchor 시점을 명확히 관리한다.
- 가능하면 stats snapshot 자체를 versioned source로 저장한다.

## 통산 첫 기록

0→1 crossing도 정상 milestone으로 취급한다.

예:
- 첫 출장
- 첫 안타
- 첫 홈런
- 첫 타점
- 첫 도루
- 첫 승
- 첫 세이브
- 첫 홀드
- 첫 탈삼진

---

# 6. 시즌 비율 기록

예:
- AVG
- OBP
- SLG
- OPS
- ERA

시즌 중에는 변동성이 크고 qualification이 필요하므로 **season finalize** 단계에서 확정 판정한다.

## Qualification

기본값 예:

```text
batting_ab_per_team_game = 3.1
pitching_ip_per_team_game = 1.0
```

실제 적용 기준은 settings/policy에서 관리한다.

## ERA direction

ERA는 lower가 좋은 기록이다.

예:

```text
ERA 2점대 이하: threshold 3.00, lower
ERA 1점대 이하: threshold 2.00, lower
ERA 0점대: threshold 1.00, lower
```

경계값의 포함 여부는 evaluator에서 명확히 통일한다.

---

# 7. 복합 기록

예:
- 20-20
- 30-30
- 40-40
- 50-50

`season_hr_sb` 같은 canonical composite stat/evaluator를 사용한다.

예:

```text
30-30 = season_hr >= 30 AND season_sb >= 30
```

복합 기록도 처음 조건이 true가 되는 시점에 한 번 생성한다.

---

# 8. 팀 기록

팀 기록은 선수 이벤트와 subject type이 다르다.

권장 subject:

```text
subject_type = team
team_id = ...
player_id = NULL
```

예:
- 선발 전원 안타
- 선발 전원 타점
- 선발 전원 득점
- 팀 노히터
- 팀 퍼펙트
- 시즌 팀 승수

선발 전원 기록은 박스스코어 라인업에서 실제 선발 명단을 기준으로 판단한다.

---

# 9. 수동 전용 / 뉴스 자동화 정책

박스스코어에서 계산할 수 없는 사건은 억지로 자동 추론하지 않는다.

예:
- MVP
- Cy Young
- Rookie of the Year
- All-Star
- Great Glove
- Platinum Stick
- 명예의 전당
- 이적
- 부상
- 일부 포스트시즌 결과

처리 우선순위:

1. 검증된 news message parser
2. 사용자 검토/승인
3. 수동 입력

자동화되지 않은 항목도 manual path로 완전히 기록할 수 있어야 한다.

---

# 10. Streak Policy

권장 JSON 예:

```json
{
  "key": "bat_hit_streak",
  "subject": "player",
  "stat": "h",
  "continue_when": {"op": ">=", "value": 1},
  "minimum_to_record": 5,
  "scope": "season"
}
```

## 필요한 정보

- policy key
- player/team subject
- 판정 stat 또는 evaluator
- streak 연장 조건
- 종료 조건
- 기록으로 보존할 최소 길이
- season boundary 처리

## 처리 순서

경기 날짜 순으로만 처리한다.

1. active streak 조회
2. 이번 경기 조건 평가
3. true → 연장 또는 신규 시작
4. false → 기존 streak 종료
5. 종료 기록이 minimum 이상이면 history 저장

수정된 과거 경기를 임의로 끼워 넣으면 이후 streak가 모두 바뀔 수 있으므로 replay가 필요하다.

---

# 11. Prediction Policy

예측은 milestone policy의 `track_from`, `near_n`, threshold를 재사용한다.

## 기본 출력

- current
- target
- remaining
- pace basis
- projected additional
- projected final
- explanation

## 시즌 예측

가능한 계산 기반:

1. 시즌 전체 평균 pace
2. 데이터가 충분할 때 최근 N경기 pace

UI에서 어느 구간을 사용했는지 반드시 설명한다.

## 통산 예측

V0.2 초기에는 복잡한 커리어 노화 모델보다 단순하고 설명 가능한 방식부터 시작한다.

예:
- 현재 시즌 pace
- 최근 여러 시즌 평균은 후속 확장

## 금지

- 투수 등판 수를 팀 경기 수와 동일시
- 데이터가 부족한데 정밀한 확률처럼 표시
- 계산 근거를 숨김

불확실성이 크면 `예상`, `추정`으로 표현한다.

---

# 12. 정책 변경과 기존 기록

정책 threshold를 변경하면 과거 이벤트의 의미가 바뀔 수 있다.

따라서 정책 변경은 다음 세 종류로 구분한다.

## A. Label-only

판정 의미 변화 없음.
자동 적용 가능.

## B. Additive

새 key 추가.
기존 데이터는 유지하고 필요 시 backfill을 수행한다.

## C. Semantic change

기존 key threshold/evaluator 변경.

이 경우:
- policy version 증가 검토
- 기존 event 재검증/backfill 전략 필요
- 사용자 기록을 조용히 삭제하지 않음

가능하면 기존 key를 유지한 채 의미를 바꾸기보다 새 key를 추가한다.

---

# 13. Bundle Update

앱 bundle의 새 정책을 사용자 데이터와 합칠 때:

1. key 기준 비교
2. 사용자가 수정하지 않은 신규 key 추가
3. 동일 key 충돌은 자동 덮어쓰기 금지
4. 변경 내역 preview 제공
5. 적용 버전 저장

---

# 14. 테스트 작성 기준

각 policy 유형마다 최소 다음 fixture를 둔다.

## Counting
- threshold 직전
- 정확히 threshold
- threshold 초과
- 이미 달성된 상태 재import

## Lower-is-better
- 경계 바로 위
- 정확히 경계
- 경계 아래

## Boolean
- false
- true
- duplicate true

## Composite
- 한 조건만 충족
- 반대 조건만 충족
- 둘 다 충족

## Streak
- 시작
- 연장
- 종료
- 최소 길이 미달
- 시즌 경계

## Prediction
- track_from 밖
- track_from 진입
- near_n 진입
- 데이터 부족

---

# 15. 초기 정책 세트의 권장 범위

V0.2의 첫 구현에서는 V0.1의 모든 세부 기준을 한 번에 옮기기보다 evaluator 종류가 충분히 검증되도록 대표 정책부터 넣는다.

## Batting
- game: H / HR / RBI / SB / cycle / grand slam
- season: H / HR / RBI / R / SB / BB
- rate: AVG / OBP / SLG / OPS
- composite: 20-20 / 30-30 / 40-40 / 50-50
- career: G / H / HR / RBI / SB

## Pitching
- game: SO / CG / SHO / no-hitter / perfect
- season: W / SO / SV / HLD / IP / ERA
- career: W / SO / SV / HLD

## Team
- all starters hit/RBI/run
- no-hitter/perfect
- season wins

이 대표 evaluator가 모두 안정된 뒤 정책 행을 확장하는 것이 좋다.

---

# 16. 정책 설계 우선순위

판단이 애매하면 다음 순서를 따른다.

1. 실제 OOTP 데이터로 확실히 판정 가능한가?
2. 중복 없이 재현 가능한가?
3. 과거 import를 replay해도 같은 결과가 나오는가?
4. 사용자에게 조건을 설명할 수 있는가?
5. 기준 숫자를 코드 수정 없이 변경할 수 있는가?

이 조건을 만족하지 못하는 기록은 자동화하지 말고 수동/검토 기반으로 남긴다.
