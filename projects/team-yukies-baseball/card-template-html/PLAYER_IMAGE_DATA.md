# PLAYER IMAGE DATA

`data/player_images.js`는 TEAM YUKIES 카드 앞면에 사용하는 선수 이미지의 **저장소 원본 데이터**입니다.

## 1. 식별 기준

각 항목의 키는 `player_ratings.csv`의 `player_id`와 정확히 같아야 합니다.

## 2. 필드

| Field | Meaning |
|---|---|
| `image_src` | 저장소 기준 이미지 경로 또는 URL. 이미지가 아직 없으면 `null`. |
| `x` | 900×1260 카드 좌표계에서의 X 오프셋(px). |
| `y` | 900×1260 카드 좌표계에서의 Y 오프셋(px). |
| `width` | 스케일 적용 전 표시 폭(px). |
| `scale` | 최종 확대/축소 배율. 기본값 1.0. |

현재 렌더러는 이미지의 종횡비를 유지하므로 별도 height 값은 저장하지 않습니다.

## 3. 좌표계

- 카드 기준 크기: 900×1260
- 원점: 카드 좌상단
- X 증가: 오른쪽
- Y 증가: 아래쪽
- 음수 좌표 허용

## 4. 이미지 파일 권장 위치

저장소에 선수 이미지를 포함하는 경우 다음 구조를 권장합니다.

```text
card-template-html/
  assets/
    players/
      <player_id>.png
```

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

## 5. 편집기와의 관계

카드 편집기에서 드래그/X/Y/Width/Scale을 조절하면 브라우저 localStorage에 임시 값이 저장됩니다.
확정 배치를 저장소에 반영할 때는 **배치 JSON 복사** 결과를 기준으로 `data/player_images.js`의 해당 선수 항목을 갱신합니다.

렌더링 우선순위는 다음과 같습니다.

1. 현재 브라우저에서 선택한 임시 이미지 파일
2. 선수 데이터의 `player_image` 값
3. `data/player_images.js`의 `image_src`

배치값은 localStorage 오버라이드가 있으면 이를 우선하고, 없으면 저장소의 `data/player_images.js` 값을 사용합니다.
