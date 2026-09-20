# Team Yukkies Card Components

카드 렌더링 그래픽을 Python 도형 코드에서 분리한 SVG 컴포넌트 세트다.

## 위치

\`templates/components/\`

## 컴포넌트

| 파일 | 용도 |
|---|---|
| \`frame_card.svg\` | 카드 전체 외곽 프레임 |
| \`frame_image.svg\` | 앞면 선수 이미지 영역 프레임 |
| \`panel_header.svg\` | 뒷면 선수 정보 헤더 |
| \`panel_section.svg\` | 레이팅/수비/구종/리포트 공용 영역 |
| \`badge_ovr.svg\` | OVR 표시 배지 |
| \`badge_position.svg\` | 앞면 등번호 + 포지션 영역 |
| \`logo_slot.svg\` | 팀 로고 슬롯 |
| \`stat_cell.svg\` | 앞면 능력치 한 칸 |
| \`bar_track.svg\` | 20–80 막대의 빈 트랙 |
| \`bar_fill.svg\` | 20–80 막대의 채움 |
| \`position_chip.svg\` | 일반 수비 포지션 칩 |
| \`position_chip_primary.svg\` | 주 포지션 강조 칩 |
| \`velocity_banner.svg\` | 투수 대표 구속 영역 |
| \`field_diamond.svg\` | 타자 수비 위치 배경 다이아몬드 |
| \`divider.svg\` | 단순 구분선 |

## 구조

\`card_renderer_modular.py\`의 \`SvgComponentLibrary\`가 SVG를 읽는다.

카드 전체를 하나의 PNG 프레임으로 쓰지 않고, 개별 SVG를 필요한 크기로 렌더링한 다음 CSV 기반 텍스트/수치와 사용자 제공 선수 이미지·팀 로고를 합성한다.

따라서 색, 선 두께, 모서리 컷, 배경색, 포인트 컬러, 프레임 형태는 Python 로직을 건드리지 않고 해당 SVG만 수정해서 바꿀 수 있다.

## 디자인 기준

- 흰색 / 연한 회색 기반
- 네이비를 기본 강조색으로 사용
- 밝은 블루는 작은 코너와 핵심 강조에만 사용
- 복잡한 금속 질감, 글로우, 강한 그림자 제거
- 얇은 선과 간단한 각진 컷 사용
- 카드 정보 계층은 장식보다 타이포그래피와 여백으로 표현

현재 \`card_studio.py\`는 기존 내부 QPainter 카드 렌더러 대신 이 모듈형 SVG 렌더러를 사용한다.
