# Team Yukkies Baseball Card Layout

## 기준

BASE 카드는 제공된 타자/투수 레퍼런스의 **스포츠 트레이딩 카드 구성**을 기준으로 한다.
앱 UI처럼 여러 독립 박스를 배치하지 않고, 선수 사진이 중심이 되며 정보 영역은 사진을 보조한다.

## 렌더 구조

- 카드 크기: **700 × 1050 (2:3)**
- 레이아웃 좌표: `card_layout.py`
- 렌더러: `card_renderer_modular.py`
- 실제 그래픽 파츠: `templates/baseball/*.svg`
- 선수 이미지/팀 로고만 사용자 에셋
- 앞면 타자 / 앞면 투수 / 뒷면 타자 / 뒷면 투수는 서로 다른 구성으로 렌더링

기존 `templates/components/`는 이전 시안용이며 새 BASE 카드 렌더러에서 사용하지 않는다.

## 앞면

### 공통 비율

- Header: y 20–196, 약 17%
- Player artwork: y 140–855, 약 68%
- Header와 artwork는 약 56px 겹침
- Summary stats: y 865–975, 약 10.5%
- Footer: y 978–1020, 약 4%

Header는 **큰 팀 로고 / 선수명·팀명 / OVR** 3영역으로 고정한다.
포지션 배지는 사진 좌측 상단에 겹쳐 배치한다.

### 타자 앞면

하단 7칸:

`CON / POW / EYE / SPD / BSR / FLD / ARM`

등번호는 포지션 배지 옆에 표시한다.

### 투수 앞면

하단 6칸:

`STF / MOV / CTL / CMD / STA / FLD`

대표 구속은 앞면에 넣지 않는다.
등번호는 상단 선수 정보 영역에 표시한다.

## 타자 뒷면

- Header: y 20–205
- Rating Breakdown: y 210–590
- Fielding Positions: y 595–825
- Scouting Report: y 830–1015

Rating은 `Contact / Power / Eye / Speed / Baserunning / Fielding / Arm`을 표시한다.

Fielding 영역:
- 왼쪽 약 40%: Primary/Secondary 포지션 목록
- 오른쪽 약 50%: 실제 야구장 형태의 다이아몬드
- 주 포지션은 파란 마커로 강조

## 투수 뒷면

- Header: y 20–205
- Rating Breakdown: y 210–535
- Fastball Velocity: y 540–610
- Pitch Mix: y 615–825
- Scouting Report: y 830–1015

구종별 개별 구속은 현재 데이터에 존재하지 않으므로 만들지 않는다.
Pitch Mix에는 구종명, 20–80 막대, 등급만 표시한다.

## 그래픽 규칙

- 레이아웃과 정보 밀도는 레퍼런스를 따른다.
- 미니멀화는 **장식 감소**로만 처리한다.
- 강한 금속 광택, 글로우, 복잡한 베벨은 사용하지 않는다.
- 흰색/연회색 바탕 + 네이비 + 제한적인 블루 포인트를 사용한다.
- 앞면 사진 면적을 줄여 정보 UI를 추가하지 않는다.
- 뒷면 섹션 사이 간격은 5px 내외로 유지해 하나의 인쇄 카드처럼 보이게 한다.

## SVG 세트

`templates/baseball/`

- `base_frame.svg`
- `front_header.svg`
- `front_photo_frame.svg`
- `position_badge.svg`
- `front_stats_7.svg`
- `front_stats_6.svg`
- `back_header.svg`
- `back_section.svg`
- `velocity_banner.svg`
- `rating_track.svg`
- `rating_fill.svg`
- `field_diamond.svg`
- `position_chip.svg`
- `position_chip_primary.svg`
- `divider.svg`
