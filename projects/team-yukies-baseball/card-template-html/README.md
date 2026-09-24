# TEAM YUKIES Card Template v7

## 데이터 원본

선수 레이팅/프로필의 소스 오브 트루스는 프로젝트 루트의 다음 파일 하나입니다.

- `../PLAYER_RATINGS.csv`

`index.html`은 시작 시 이 CSV를 자동 로드합니다.
브라우저 보안 정책상 `file://`로 직접 열면 상대 경로 CSV의 자동 fetch가 차단될 수 있으므로, 자동 로드는 로컬 HTTP 서버(예: VS Code Live Server) 실행을 기준으로 합니다. 상단 CSV 파일 선택은 수동 대체 경로로 유지합니다.

다음 파일들은 더 이상 선수 레이팅 원본으로 사용하지 않습니다.

- `data/player_ratings.csv` — 제거
- `data/player-data.js` — 제거

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
