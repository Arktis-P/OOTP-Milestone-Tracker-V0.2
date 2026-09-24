# Team Yukkies Card Studio — UI / Usage

## 목적

`PLAYER_RATINGS.csv`의 선수를 선택하고 카드 앞면/뒷면을 즉시 미리본 뒤 PNG로 저장하는 로컬 데스크톱 도구다.

사용자는 카드 프레임, 능력치 박스, 수비 다이아몬드, 투수 구종 패널 등의 그래픽 요소를 직접 만들지 않는다. 해당 요소는 `card_studio.py`의 렌더러가 자동으로 그린다.

사용자가 준비하는 외부 이미지 에셋은 두 종류뿐이다.

- 선수 이미지
- 팀 로고

## UI 구조

### 좌측 — 선수

- CSV에 존재하는 선수 목록
- 이름 / 작품명 검색
- 선택 즉시 중앙 카드 갱신

### 중앙 — 카드 미리보기

- `앞면` / `뒷면` 전환
- 실제 PNG와 같은 렌더러 사용
- 선수 이미지나 팀 로고가 없더라도 빈 슬롯이 표시되어 카드 구조를 확인할 수 있음

### 우측 — 선수 정보 / 에셋 / 내보내기

- CSV에서 불러온 기본 선수 정보 확인
- 선수 이미지 등록 / 교체
- 팀 로고 등록 / 교체
- 현재 면 PNG 저장
- 앞면 + 뒷면 PNG 동시 저장

## 에셋 저장 규칙

앱에서 이미지를 선택하면 원본 확장자와 관계없이 PNG로 변환해 아래 위치에 저장한다.

```text
assets/players/{player_id}.png
assets/teams/{team_id}.png
```

따라서 같은 팀의 다른 선수를 선택하면 기존 팀 로고가 자동으로 재사용된다.

CSV에는 이미지 경로를 저장하지 않는다.

## 카드 자동 구성

### 앞면

- 선수 이미지
- 팀 로고
- 선수명 / 작품 / 팀명
- OVR / 등번호 / 포지션 / 투타
- 타자: CON / POW / GAP / EYE / SPD / FLD
- 투수: STF / MOV / CTL / CMD / STA / VEL

### 뒷면

공통:

- 선수 프로필
- 상세 능력치 막대
- Scouting Report

타자:

- 등록된 `def_*` 값으로 수비 다이아몬드 자동 생성
- 주 포지션 강조

투수:

- Arm Slot
- 대표 평균 구속
- 값이 있는 구종만 자동 표시

## 실행

저장소 루트에서:

```bash
python projects/team-yukkies-baseball/card_studio.py
```

다른 CSV를 바로 열고 싶다면:

```bash
python projects/team-yukkies-baseball/card_studio.py --csv path/to/PLAYER_RATINGS.csv
```

필요 패키지는 저장소 기본 의존성인 `PySide6`다.

## 디자인 원칙

- 밝은 회색 / 흰색 기반의 데스크톱 툴 UI
- 한 가지 네이비 포인트 컬러만 사용
- 그라데이션, 글로우, 과도한 라운드 카드 UI 사용 금지
- 장식보다 목록 → 미리보기 → 작업 패널의 정보 구조 우선
- 카드 자체도 BASE 타입은 과도한 장식 없이 스포츠 데이터 카드처럼 유지
