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


## 타이포그래피 잠금 규칙

레퍼런스 느낌을 유지하기 위해 텍스트도 레이아웃 자산과 동일하게 고정 규격으로 취급한다.

- 렌더링 기준 캔버스: 900 × 1600
- 글자 크기 단위: **QFont pixel size**
- point size 사용 금지: 모니터 DPI에 따라 미리보기/PNG 비율이 달라지는 것을 방지한다.
- 디스플레이 계열: `Bahnschrift` + stretch 76
- 일반 한글 본문: `Malgun Gothic`
- 영어 Scouting Report도 레퍼런스처럼 폭이 좁게 보이도록 condensed 렌더 사용
- 선수명만 지정 영역을 넘을 경우 자동 축소하며, 나머지 핵심 숫자/라벨은 고정 크기를 유지한다.

주요 크기:

| 요소 | px |
|---|---:|
| 앞면 선수명 | 60 (최소 48) |
| 팀명 | 30 |
| OVR 라벨 / 숫자 | 40 / 122 |
| 포지션 / 등번호 / 투타 | 66 / 66 / 52 |
| 하단 스탯 라벨 / 숫자 | 30 / 62 |
| 뒷면 선수명 | 58 (최소 46) |
| 뒷면 프로필 | 33 |
| 섹션 타이틀 | 42 |
| Rating 라벨 / 값 | 32 / 34 |
| Scouting Report 본문 | 26 |

좌표와 글꼴 크기는 `card_layout_v2.py`의 `TYPOGRAPHY`와 레이아웃 사전을 단일 소스로 사용한다.


## 2026-09-20 preview tuning

현재 앱의 약 450 × 800 미리보기 캡처를 다시 기준으로 검토해 다음을 조정했다.

- 섹션 타이틀이 장식 프레임과 충돌하지 않도록 54px → 42px
- Rating 라벨/수치를 각각 32px / 34px로 축소
- Pitch Arsenal 라벨/수치도 한 단계 축소
- 앞면 선수명/팀명/포지션/등번호를 레퍼런스 대비 과대 표시되지 않도록 축소
- Scouting Report 본문은 26px 비압축 한글 폰트로 렌더해 더 작은 크기에서도 읽기 쉽게 처리
- Condensed stretch는 76 → 82로 완화해 영문 글자가 지나치게 찌그러져 보이지 않도록 처리


## 2026-09-20 sports-card refinement pass

현재 앱 미리보기와 실제 스포츠 카드/게임형 선수 카드의 정보 위계를 다시 비교해 다음 원칙으로 수정했다.

- 뒷면 섹션의 큰 파란 코너 브래킷을 제거하고 얇은 금속 프레임 + 블루 헤어라인으로 축소
- 뒷면은 "게임 메뉴 UI"보다 인쇄된 정보 카드처럼 조용하게 구성
- 한글은 Condensed 영문 폰트를 강제하지 않으며, Malgun Gothic 계열의 자연스러운 폭을 사용
- OVR/포지션/스탯 라벨 등 영문·숫자만 스포츠 카드용 Condensed 계열 사용
- Scouting Report는 기본 22px, 긴 문장은 17px까지 자동 축소
- 뒷면 프로모션성 slogan은 제거
- 반복되는 팀명 footer를 Scouting Report 내부에서 제거해 실제 카드 뒷면처럼 정보 밀도를 낮춤
- 타자/투수 뒷면은 동일한 시각 문법을 공유하되, 내용만 Fielding / Pitching으로 분기
