# Team Yukkies Baseball Card Template V2 — Reference Spec

## 목적

첨부 레퍼런스 4장(타자 앞/뒤, 투수 앞/뒤)을 기준으로, 타자와 투수가 **같은 카드 브랜드/프레임을 공유**하면서 내용만 달라지는 9:16 템플릿 체계를 정의한다.

V2 준비 단계에서는 기존 실행 경로(`card_layout.py` + `templates/baseball/`)를 건드리지 않는다. 실제 GUI 연결은 다음 구현 단계에서 `card_layout_v2.py`와 `templates/baseball_v2/`를 사용해 교체한다.

## 레퍼런스에서 고정할 것

- 원본 이미지 크기: 941 × 1672
- 실질 비율: 9:16 세로 카드
- 공통 외곽: 은색 얇은 프레임 + 안쪽 네이비 라인 + 흰색/연회색 바탕
- 공통 포인트: 네이비 + 선명한 블루
- 앞면: 선수 이미지가 가장 큰 면적을 차지
- 앞면 상단: 팀 로고 / 선수명·팀명 / OVR
- 앞면 사진 위: 포지션 + 등번호 + 투타 배지
- 앞면 하단: 6개 핵심 스탯
- 뒷면 상단: 팀 로고 / 선수명 / 팀 / 프로필 / 등번호
- 뒷면 본문: 20–80 막대 + 역할별 추가 영역 + Scouting Report
- 타자/투수는 텍스트와 데이터 구성이 달라도 같은 외곽 프레임, 패널, 선 두께, 컬러, 여백 체계를 사용

## V2 기준 캔버스

정규화된 제작 캔버스는 **900 × 1600**으로 한다.

이유:
- 정확한 9:16
- GUI 미리보기/PNG 출력에서 정수 좌표 사용이 편함
- 첨부 레퍼런스 941 × 1672와 거의 동일한 세로 비례
- 최종 출력 해상도는 배수 스케일링 가능

모든 좌표는 `card_layout_v2.py`를 단일 기준으로 사용한다.

## 공통 스타일 토큰

- `ink`: #10224A
- `navy`: #123A67
- `blue`: #2376D8
- `blue_bright`: #3688EA
- `silver`: #C9D0D7
- `silver_dark`: #8E9AA5
- `paper`: #F7F8FA
- `paper_alt`: #EEF2F6
- `track`: #D7DDE4
- `white`: #FFFFFF

장식은 레퍼런스의 실제 인쇄 카드 느낌을 우선한다. 얇은 금속 다중 프레임, 네이비/블루 코너 웨지, 각진 배지, 은색 하이라이트를 적극적으로 사용하되 사진과 수치 가독성을 해치지 않는다.

## 레이어 순서

### 앞면

1. `card_shell`
2. 선수 사진
3. `photo_frame`
4. `front_header`
5. 팀 로고
6. 이름 / 팀명 / OVR
7. `position_badge` + 등번호 + 투타
8. `front_stats_rail`
9. 6개 스탯 텍스트
10. 하단 divider + 팀명

### 뒷면

1. `card_shell`
2. `back_header`
3. 팀 로고 + 선수 프로필
4. `section_panel` 반복
5. 20–80 그래프
6. 타자: field diamond / 투수: velocity banner + pitch arsenal
7. scouting report
8. 하단 divider + 팀명

## 앞면 영역

- Header: (28, 28, 844, 260)
- Photo outer: (34, 220, 832, 1122)
- Photo inner: (42, 228, 816, 1106)
- Position badge: (40, 278, 128, 112)
- Number area: (170, 284, 110, 90)
- Handedness area: (742, 284, 114, 74)
- Stats rail: (28, 1346, 844, 180)
- Footer: (28, 1528, 844, 44)

Header가 사진 위로 약 68px 겹치도록 하여 레퍼런스의 트레이딩 카드 느낌을 유지한다.

## 뒷면 영역

### 공통

- Header: (28, 28, 844, 268)

### 타자

- Ratings: (28, 302, 844, 550)
- Fielding: (28, 858, 844, 330)
- Scouting: (28, 1194, 844, 378)

### 투수

- Ratings: (28, 302, 844, 510)
- Velocity: (28, 818, 844, 92)
- Pitch arsenal: (28, 916, 844, 280)
- Scouting: (28, 1202, 844, 370)

## 변형 원칙

공통 프레임을 복제해 타자/투수 전용 SVG를 만들지 않는다.

- 공통: shell, header, photo frame, section panel, stat rail, rating track/fill, divider, position badge
- 타자 전용: field diamond와 타자 데이터 매핑
- 투수 전용: velocity banner와 pitch arsenal 데이터 매핑

즉 4개의 카드 타입은 **4개의 별도 디자인**이 아니라 **하나의 디자인 시스템 + 4개의 조합 규칙**으로 관리한다.

## 구현 전 체크

- GUI 카드 미리보기 비율을 9:16으로 고정
- 기존 700 × 1050 레이아웃 값과 혼용 금지
- 텍스트는 SVG에 박아 넣지 않고 렌더러가 출력
- SVG는 프레임/패널/바/필드 등 재사용 그래픽만 담당
- 선수 이미지 crop은 Photo inner 영역에서 cover 방식
- 팀 로고는 contain 방식
- 타자/투수 양쪽 모두 동일한 shell과 header family 사용
