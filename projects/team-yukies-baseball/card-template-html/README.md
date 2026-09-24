# TEAM YUKIES Card Template v7

## 데이터 원본

선수 생성·평가·파생값 계산 규칙은 프로젝트 루트의 `../PLAYER_CREATION_GUIDELINES.md`를 최상위 기준으로 사용합니다.

선수 레이팅/프로필의 소스 오브 트루스는 프로젝트 루트의 다음 파일 하나입니다.

- `../PLAYER_RATINGS.csv`

`index.html`은 시작 시 이 CSV를 자동 로드합니다.
브라우저 보안 정책상 `file://`로 직접 열면 상대 경로 CSV의 자동 fetch가 차단될 수 있으므로, 자동 로드는 로컬 HTTP 서버(예: VS Code Live Server) 실행을 기준으로 합니다. 상단 CSV 파일 선택은 수동 대체 경로로 유지합니다.

다음 파일들은 더 이상 선수 레이팅 원본으로 사용하지 않습니다.

- `data/player_ratings.csv` — 제거
- `data/player-data.js` — 제거

## 프리뷰 실행

현재 실제 카드 확인용 엔트리 포인트는 **`index.html`** 입니다.

`team-yukies-card-example.html`은 과거 정적 예제 파일이었으며, 현재는 `index.html`로 이동시키는 호환용 진입점만 유지합니다.

### Windows 권장

프로젝트 루트의 다음 파일을 더블클릭합니다.

```text
projects/team-yukies-baseball/open-card-preview.bat
```

실행하면 로컬 HTTP 서버를 열고 브라우저에서 다음 주소를 자동으로 엽니다.

```text
http://127.0.0.1:8765/card-template-html/
```

서버 창을 닫으면 프리뷰 서버도 종료됩니다.

### 수동 실행

`projects/team-yukies-baseball` 폴더에서:

```bat
py -m http.server 8765 --bind 127.0.0.1
```

그 뒤 브라우저에서 `http://127.0.0.1:8765/card-template-html/`을 엽니다.

`index.html`을 파일 탐색기에서 직접 더블클릭하는 방식(`file://`)은 브라우저 보안 정책 때문에 `../PLAYER_RATINGS.csv` 자동 로드가 막힐 수 있으므로 권장하지 않습니다.

## 이미지 데이터

선수 투명 PNG의 파일 경로와 앞면 배치값은 레이팅 CSV와 분리합니다.

- `data/player_images.js`
- `PLAYER_IMAGE_DATA.md`

레이어 순서:

```text
1. front-background.png
2. 선수 투명 PNG
3. front-batter-overlay.png / front-pitcher-overlay.png
4. 이름 / OVR / 번호 / 능력치 텍스트
```

카드 좌표계는 900×1260이며, 편집기에서 이미지 선택/드래그앤드롭, 직접 드래그, X/Y/Width/Scale 조절, 1px 이동, Reset, 제거, 배치 JSON 복사를 지원합니다.

## 폰트

CSS는 저장소에 올라온 실제 파일명을 직접 참조합니다.

- `fonts/esamanru Light.ttf` — Light
- `fonts/esamanru Medium.ttf` — Medium
- `fonts/esamanru Bold.ttf` — Bold


## v8 UI / PNG 저장

프리뷰 화면은 좌측 선수 목록 + 우측 카드 프리뷰 구조를 사용합니다.

- 좌측 선수 이름을 클릭하면 해당 선수의 앞/뒷면 카드가 즉시 표시됩니다.
- 상단 Preview 슬라이더로 브라우저 표시 크기를 35%–100% 사이에서 조절할 수 있습니다.
- 확대/축소는 화면 표시만 바꾸며 저장 해상도에는 영향을 주지 않습니다.
- `앞/뒤 PNG 저장` 버튼은 현재 선택된 선수의 카드만 저장합니다.
- 파일명:
  - `{serial}_front.png`
  - `{serial}_back.png`
- PNG는 900×1260 크기로 생성하며 알파 채널을 지원합니다.

PNG 변환에는 브라우저에서 `html-to-image`를 로드합니다. 프리뷰 서버를 실행한 상태에서 인터넷 연결이 필요합니다.
