# Team Yukkies Baseball Card Layout

## 기준

BASE 카드는 제공된 타자/투수 레퍼런스 4장의 **9:16 스포츠 트레이딩 카드 구성**을 기준으로 한다.
타자와 투수는 세부 데이터만 달라지고 외곽 프레임, 헤더, 패널, 선 두께, 컬러 체계는 공유한다.

## 렌더 구조

- 카드 크기: **900 × 1600 (9:16)**
- 레이아웃 좌표: `card_layout_v2.py`
- 렌더러: `card_renderer_modular.py`
- 그래픽 파츠: `templates/baseball_v2/`
- 미리보기와 PNG 내보내기는 같은 `ModularCardRenderer.render()` 결과를 사용
- 선수 이미지/팀 로고만 사용자 에셋
- 기존 `card_layout.py` / `templates/baseball/`은 레거시 자산으로 유지

## 앞면

공통 흐름은 다음과 같다.

1. 은색 외곽 프레임
2. 큰 선수 사진
3. 사진 위로 겹치는 상단 헤더
4. 좌상단 포지션 + 등번호
5. 우상단 투타
6. 우측 OVR 블록
7. 하단 6칸 스탯 스트립
8. 하단 팀명

### 타자

`CON / POW / GAP / EYE / SPD / FLD`

### 투수

`STF / MOV / CTL / CMD / STA / VEL`

VEL은 실제 km/h를 표시한다.

## 뒷면 공통

- 상단: 팀 로고 / 선수명 / 팀명 / 프로필 / 원작 / 등번호
- 20–80 Detailed Ratings
- 역할별 전용 영역
- Scouting Report

### 타자

- Ratings: Contact / Power / Gap / Eye / Baserunning / Stealing / Arm
- Fielding Positions: 활성 `def_*`만 표시
- 다이아몬드 위 주 포지션은 블루 마커, 부 포지션은 화이트 마커
- Scouting Report

### 투수

- Ratings: Stuff / Movement / Control / Command / Stamina / Fielding
- Fastball Velocity
- Pitch Arsenal
- Scouting Report

Pitch Arsenal은 구종별 개별 구속 없이 20–80 등급만 표시한다.

## 그래픽 규칙

- 흰색/연회색 바탕 + 네이비 + 선명한 블루 + 얇은 은색 프레임
- 장식보다 선수 이미지와 데이터 위계가 우선
- 헤더와 선수 사진을 일부 겹쳐 단일 카드처럼 보이게 한다
- 독립 앱 패널처럼 보이는 큰 여백을 피한다
- 숫자와 라벨은 폭이 좁은 스포츠 카드 계열 서체 느낌으로 렌더한다
- 긴 선수명은 자동 축소하여 헤더 폭 안에 유지한다

## SVG 세트

`templates/baseball_v2/`

### common
- `card_shell.svg`
- `front_header.svg`
- `photo_frame.svg`
- `position_badge.svg`
- `front_stats_rail.svg`
- `back_header.svg`
- `section_panel.svg`
- `rating_track.svg`
- `rating_fill.svg`
- `divider.svg`

### batter
- `field_diamond.svg`

### pitcher
- `velocity_banner.svg`
