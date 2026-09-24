# Team Yukies Baseball

이 디렉터리의 **현재 카드 작업 기준은 `card-template-html/` 하나뿐**입니다.

## Active

- `PLAYER_CREATION_GUIDELINES.md` — 선수 생성/평가 기준
- `PLAYER_RATINGS.csv` — 선수 레이팅·프로필의 단일 원본 데이터
- `card-template-html/` — 현재 TEAM YUKIES 카드 템플릿 및 편집기
  - `index.html`
  - `team-yukies-card.css`
  - `team-yukies-card.js`
  - `DATA_SCHEMA.md`
  - `PLAYER_IMAGE_DATA.md`
  - `data/player_images.js`
  - `assets/`
  - `fonts/`

`card-template-html/index.html`은 시작 시 **`../PLAYER_RATINGS.csv`**를 자동 로드합니다.
`card-template-html/data/`에는 별도의 선수 레이팅 CSV를 두지 않습니다.

새 카드 템플릿 작업은 **반드시 `card-template-html/` 기준으로 진행**합니다.

## Archive / 휴지통

이전 Python/SVG 기반 카드 템플릿과 관련 문서는 모두 다음 위치로 이동했습니다.

`archive/legacy-card-template/`

Archive는 과거 구현 확인용이며 **현재 구현의 소스 오브 트루스로 사용하지 않습니다.**
