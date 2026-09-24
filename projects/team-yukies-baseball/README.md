# Team Yukies Baseball

이 디렉터리의 현재 선수/카드 작업 기준은 다음 네 파일이다.

- `PLAYER_CREATION_GUIDELINES.md` — 서브컬처 캐릭터를 야구선수로 해석하고 레이팅을 결정하는 기준
- `PLAYER_RATINGS_WORKFLOW.md` — 결정한 값을 CSV에 기록·재계산·검증하는 절차
- `PLAYER_RATINGS.csv` — 선수 데이터 단일 원본
- `card-template-html/` — 현재 TEAM YUKIES 카드 템플릿

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

## Archive

이전 Python/SVG 기반 카드 템플릿과 과거 문서는:

`archive/legacy-card-template/`

에 보관하며 현재 기준으로 사용하지 않는다.
