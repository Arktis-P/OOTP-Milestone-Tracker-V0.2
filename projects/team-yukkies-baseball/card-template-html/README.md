# TEAM YUKIES Card Template v7

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

상단 Player Image에서:

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

를 지원합니다.

기본값:

```text
X = 0
Y = 0
Width = 900
Scale = 1.0
```

배치값은 `player_id`별로 브라우저 localStorage에 저장됩니다.
따라서 선수마다 다른 위치와 크기를 유지할 수 있습니다.

예:

```json
{
  "player_id": "himekawa_yuki",
  "player_image_layout": {
    "x": -18,
    "y": 36,
    "width": 945,
    "scale": 1
  }
}
```

## 향후 CSV 확장용 컬럼

```text
player_image
player_image_x
player_image_y
player_image_width
player_image_scale
```

를 추가하면 최종 배치를 CSV 데이터로 옮길 수 있습니다.
