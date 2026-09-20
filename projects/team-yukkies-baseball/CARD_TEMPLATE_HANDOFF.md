# Team Yukkies Player Card — Design & Automation Handoff

## 1. 목적

팀 윳키즈 선수 카드의 디자인과 자동 생성 시스템을 다음 대화/작업자가 바로 이어서 설계할 수 있도록 현재까지 확정된 요구사항을 정리한다.

이 문서는 카드 디자인을 확정하는 문서가 아니라, **템플릿 제작 및 자동 렌더링 작업의 핸드오프 기준**이다.

---

## 2. 사용자 피로 최소화 원칙

최종 목표는 사용자가 카드 제작을 위해 Figma, Photoshop, SVG 편집 등을 직접 하지 않아도 되는 것이다.

사용자는 최종적으로 다음만 제공하면 되어야 한다.

1. `PLAYER_RATINGS.csv`에 기록된 선수 정보
2. 선수 이미지
3. 팀 로고

렌더러가 나머지를 자동 처리한다.

### 에셋 규칙

- 선수 이미지: `assets/players/{player_id}.png`
- 팀 로고: `assets/teams/{team_id}.png`

CSV에 이미지 경로를 반복 입력하지 않는다.

---

## 3. 카드 템플릿 종류

기본 템플릿은 4종으로 유지한다.

- `batter_front`
- `batter_back`
- `pitcher_front`
- `pitcher_back`

특수 카드가 추가되더라도 기본 정보 배치는 최대한 유지하고 프레임/배경/라벨만 변형하는 방향을 우선한다.

예상 특수 카드 타입:

- BASE
- ALL_STAR
- GOLD_GLOVE
- MVP
- ROOKIE
- SPECIAL

현재는 BASE만 사용한다.

---

## 4. 카드 앞면 요구사항

### 공통

- 선수 이름
- 팀 이름
- 팀 로고
- 종합 능력치(OVR)
- 주 포지션
- 등번호
- 투타 정보
- 선수 이미지
- 6개 핵심 능력치 요약

현재는 별도의 선수 유형 라벨(예: Power Hitting 3B, Power Starter)을 앞면에 표시하지 않는다.

추후 특수 카드 타입이 생기면 해당 영역을 ALL-STAR, GOLD GLOVE 등의 카드 타입 라벨로 활용할 수 있다.

### 타자 앞면 6개 요약

- CON = Contact
- POW = Power
- GAP = Gap
- EYE = Eye
- SPD = (Baserunning + Stealing) / 2
- FLD = 주 포지션의 `def_*`

### 투수 앞면 6개 요약

- STF = Stuff
- MOV = Movement
- CTL = Control
- CMD = Command
- STA = Stamina
- VEL = 대표 속구 평균 구속(km/h)

VEL은 20–80 수치가 아니라 실제 km/h로 표시한다.

---

## 5. 카드 뒷면 요구사항

### 타자

- 선수 정보 요약
- 상세 20–80 능력치 막대 그래프
  - Contact
  - Power
  - Gap
  - Eye
  - Baserunning
  - Stealing
  - Arm
- 수비 위치 다이아몬드
- C / 1B / 2B / 3B / SS / LF / CF / RF 중 값이 있는 위치만 표시
- 각 위치 마커에 종합 수비 능력치 표기
- Scouting Report

별도 Notes 영역은 두지 않는다.

### 투수

- 선수 정보 요약
- 투타
- 투구폼(arm slot)
  - OVERHAND
  - THREE_QUARTER
  - SIDEARM
  - UNDERHAND
- 상세 20–80 능력치 막대 그래프
  - Stuff
  - Movement
  - Control
  - Command
  - Stamina
  - Pitcher Fielding
- 대표 속구 평균 구속(km/h)
- 구종별 20–80 능력치
- Scouting Report

구종별 개별 구속은 표시하지 않는다.

별도 Notes 영역은 두지 않는다.

---

## 6. 수비 위치 시각화

타자 카드 뒷면에는 간소화한 야구 필드 다이아몬드를 사용한다.

렌더러는 CSV의 다음 값을 읽는다.

- `def_c`
- `def_1b`
- `def_2b`
- `def_3b`
- `def_ss`
- `def_lf`
- `def_cf`
- `def_rf`

값이 있는 포지션만 다이아몬드 위에 마커를 출력한다.

권장 표현:

- 주 포지션: 강조된 마커
- 부 포지션: 일반 마커
- 마커 내부: 포지션명 + 수비 등급
- 값이 없는 위치: 미표시

---

## 7. 투수 구종 시각화

구종 열은 `CARD_DATA_SCHEMA.md`에 정의된 Statcast 기반 구종 분류를 사용한다.

값이 있는 구종만 카드에 출력한다.

예:

- Four-Seam Fastball 65
- Slider 60
- Curveball 55
- Changeup 50

구종별 개별 km/h는 저장하거나 표시하지 않는다.

대표 속구 평균 구속은 `velocity_kmh` 하나만 사용한다.

---

## 8. 권장 템플릿 구현 방식

사용자에게 Figma 작업을 요구하지 않는다.

권장 구조:

```text
projects/team-yukkies-baseball/
├─ assets/
│  ├─ players/
│  └─ teams/
├─ templates/
│  ├─ batter_front.svg
│  ├─ batter_back.svg
│  ├─ pitcher_front.svg
│  └─ pitcher_back.svg
├─ output/
└─ scripts/
   └─ render_cards.py
```

### 권장 방식

- 템플릿: SVG 또는 HTML/SVG 혼합
- 데이터: `PLAYER_RATINGS.csv`
- 렌더러: Python
- 최종 출력: PNG

디자인 변경은 템플릿 코드 수정으로 처리한다.

사용자가 직접 그래픽 편집기를 사용할 필요가 없어야 한다.

---

## 9. 자동 렌더링 목표 UX

최종 사용 흐름:

```text
1. 선수 레이팅 확정
2. PLAYER_RATINGS.csv에 행 추가
3. assets/players/{player_id}.png 추가
4. 필요할 때 assets/teams/{team_id}.png 추가
5. 렌더 실행
6. front / back PNG 자동 생성
```

예:

```text
python scripts/render_cards.py --player himekawa_yuki
```

예상 출력:

```text
output/himekawa_yuki_front.png
output/himekawa_yuki_back.png
```

---

## 10. 디자인 방향

현재 시안의 방향:

- 세로형 스포츠 카드
- 단순한 은색/흰색/팀 컬러 프레임
- 선수 이미지가 앞면의 대부분을 차지
- OVR과 주 포지션은 즉시 읽히도록 강조
- 하단에 6개 요약 능력치
- 뒷면은 데이터 카드처럼 정돈
- 과도한 장식 최소화

향후 카드 타입별 프레임 변형은 가능하되 BASE 템플릿은 최대한 단순하게 유지한다.

---

## 11. 관련 문서

- `PLAYER_CREATION_GUIDELINES.md`
- `PLAYER_RATINGS.csv`
- `CARD_DATA_SCHEMA.md`

실제 카드 템플릿 구현 전에는 반드시 이 세 문서와 본 문서를 함께 확인한다.
