# Team Yukies Baseball

선수 생성·평가 작업은 먼저 **`PLAYER_GUIDE.md`**를 확인한다. 이 파일이 어떤 단계에서 어떤 상세 문서를 참조해야 하는지 안내하는 단일 진입점이다.

## 현재 기준 파일

- `PLAYER_GUIDE.md` — 선수 생성 작업의 통합 진입 문서
- `docs/PLAYER_CREATION_GUIDELINES.md` — 포지션·역할·레이팅 및 OVR 기준
- `docs/PLAYER_PROFILE_GUIDELINES.md` — 신장·체중·생일·출생지 추론 기준
- `docs/PLAYER_TRAIT_GUIDELINES.md` — Trait 1/2/3 기준
- `docs/PLAYER_NUMBER_GUIDELINES.md` — 등번호 선정 기준
- `docs/PLAYER_RATINGS_WORKFLOW.md` — CSV 기록·계산·검증 절차
- `PLAYER_RATINGS.csv` — 선수 데이터 단일 원본
- `card-template-html/` — 현재 Team Yukies 카드 템플릿

## 작업 순서

```text
PLAYER_GUIDE.md 확인
→ 필요한 docs 상세 기준만 참조
→ PLAYER_RATINGS.csv 갱신
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
