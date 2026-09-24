# TEAM YUKIES Card Template v7

## 데이터 원본

현재 카드 템플릿에서 사용하는 저장소 데이터는 다음 두 파일을 기준으로 합니다.

- `data/player_ratings.csv` — 선수 레이팅/프로필 CSV
- `data/player_images.js` — 선수별 이미지 경로와 앞면 배치값
- 상세 이미지 데이터 규칙: `PLAYER_IMAGE_DATA.md`

## 선수 이미지 위치

선수 투명 PNG는 다음 레이어에 들어갑니다.

```text
1. 앞면 경기장 배경
2. 선수 PNG
3. 타자/투수 앞면 overlay
4. 이름/OVR/번호/능력치 텍스트
```

따라서 선수는 경기장 위에 있지만 카드 프레임과 이름판 아래에 있습니다.

## 원본 PNG 권장

- 투명 PNG
- 세로 1200px 이상 권장
- 캐릭터 주위 투명 여백은 가능하면 적게
- 원본이 900×1260일 필요는 없음

## 위치 조절

카드 좌표계는 900×1260입니다.

상단 Player Image에서 다음을 지원합니다.

- 이미지 파일 선택
- 카드 위로 이미지 드래그앤드롭
- 선수 이미지를 마우스로 직접 드래그
- X / Y 숫자 입력
- Width 입력
- Scale 입력
- 방향 버튼으로 1px씩 이동
- Reset
- 이미지 제거
- 현재 배치 JSON 복사

기본값:

```text
X = 0
Y = 0
Width = 900
Scale = 1.0
```

브라우저에서 조절한 값은 `player_id`별 localStorage에 임시 저장됩니다.
저장소에서 공유할 확정값은 `data/player_images.js`에 기록합니다.

예:

```js
himekawa_yuki: {
  image_src: "./assets/players/himekawa_yuki.png",
  x: -18,
  y: 36,
  width: 945,
  scale: 1
}
```

기존 오타 키 `team-yukkies-image-layout:*`가 남아 있으면 렌더러가 새 `team-yukies-image-layout:*` 키로 자동 이전합니다.
