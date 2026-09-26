# Team Yukies Baseball

이 디렉터리의 현재 선수/카드 작업 기준은 다음 네 파일이다.

- `PLAYER_CREATION_GUIDELINES.md` — 서브컬처 캐릭터를 야구선수로 해석하고 레이팅을 결정하는 기준
- `PLAYER_RATINGS_WORKFLOW.md` — 결정한 값을 CSV에 기록·재계산·검증하는 절차
- `PLAYER_RATINGS.csv` — 선수 데이터 단일 원본
- `card-template-html/` — 현재 Team Yukies 카드 템플릿

## 작업 순서

```text
캐릭터 조사
→ PLAYER_CREATION_GUIDELINES 기준으로 원본 레이팅 결정
→ 계산값(speed / 야수 fielding / overall / serial) 계산
→ PLAYER_RATINGS_WORKFLOW에 따라 CSV 갱신
→ card-template-html에서 카드 확인
```

## 카드 템플릿

`card-template-html/index.html`은 시작 시 `../PLAYER_RATINGS.csv`를 자동 로드한다.

이미지 경로와 선수 이미지 배치는 `card-template-html/data/player_images.js`에서 별도 관리한다.

## Windows 실행

브랜딩된 기본 실행 진입점은 다음 파일이다.

```text
Team Yukies Card Preview.exe
```

- 아이콘 원본: `card-template-html/assets/app-icon.png`
- Windows ICO: `card-template-html/assets/app-icon.ico`
- 런처 소스/빌드: `launcher/`
- `open-card-preview.bat`는 호환용/수동 실행 경로로 유지한다.

Windows의 `.bat` 파일 아이콘은 파일 자체에 개별 아이콘을 내장할 수 없고 파일 연결 아이콘을 사용한다. 따라서 사용자에게 노출되는 앱 실행 아이콘은 `Team Yukies Card Preview.exe`에 적용한다.

GitHub Actions의 런처 워크플로는 빌드/아이콘 검증만 수행하며 저장소에 자동 커밋하거나 푸시하지 않는다.

## Archive

이전 Python/SVG 기반 카드 템플릿과 과거 문서는:

`archive/legacy-card-template/`

에 보관하며 현재 기준으로 사용하지 않는다.
