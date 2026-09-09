# 말랑이의 방 — 배경 일러스트 생성 프롬프트 v1 (보관)

> **2026-09-09 상태:** 방은 **픽셀 테마(Kenney 타일 + 블롭, `scripts/pixel-room/build.py`)**로 확정됐다. 이 문서는 `MALLANG_THEME`(일러스트) 토글을 되살릴 때만 쓴다.

> 2026-09-09 · 세계관: saju-mbti-report 말랑이(파스텔 과슈 동화 아틀라스). 스타일 앵커는 saju `public/village/hero-neighbors-desktop.jpg`(-sref).
> 원칙(saju brand-core 승계): **모든 아트는 드롭인 슬롯.** 코드 폴백(`MallangRoom.module.css`)으로 먼저 돌고, 그림이 도착하면 `public/room/bg.jpg` 한 장으로 교체. 아트가 개발을 블로킹하지 않는다.

## 결정 기록 (2026-09-09)

| 항목 | 결정 |
|---|---|
| 공간 | 싸이월드 미니룸식 **한 칸 방**. 마을이 아니라 방 — 걷기 마찰 없음, 모바일 한 화면 |
| 시점 | **정면 살짝 위(돌하우스 컷어웨이)**. 아이소메트릭 X — 말랑이는 시점 요구가 없고, 핫스팟 %좌표가 단순해짐 |
| 가구 | **배경에 박음** + 코드 핫스팟. 상태 변화(점등·D-1)는 코드 오버레이. 가구 재배치·꾸미기는 v1 범위 밖(개별 컷아웃 생성은 후속) |
| 캐릭터 | 배경에 **그리지 않는다**. 말랑이 PNG를 코드가 얹음(hop 애니메이션). 유저 미니미 = 본인 MBTI 말랑이, 에이전트 = saju v2(MBTI×오행) 다솜·fire / 구담·water / 설이·wood / 까론·earth |
| 규격 | **3:2 가로**, 1920×1280 이상, jpg. 데스크톱·모바일 공통(좌표계 하나) |

## 프롬프트

```
interior of a small cozy study room for a cute mobile game, front view with a
slightly elevated dollhouse cutaway perspective, one back wall and a wooden floor,
pastel gouache and watercolor picture-book illustration, very subtle warm paper
texture, thin soft ink outlines, smooth rounded gently plump furniture shapes with
no sharp edges, squishy huggable feel like mochi,

warm muted palette softened to pastel: cream walls, honey wood floor, soft coral
rug, sage green sofa, butter yellow and mint accents, gentle top-left daylight
from an arched window,

furniture, each with generous empty space around it and a clear simple silhouette
that reads at small size:
- a tall wooden bookshelf filled with pastel books and folders against the left
  wall, floor to mid-height
- a small wooden desk with a closed laptop and a cup, a little wooden chair in
  front of it, left-center
- an arched window with a small potted plant on the sill, center of the back wall
- a cork bulletin board with a few blank pastel sticky notes and a pinned paper,
  right-center of the back wall
- a single bed with a cream pillow and a soft steel-blue blanket against the right
  wall
- a two-seat sage green sofa with two round cushions, lower right
- a round soft coral rug in the lower center, a leafy potted plant in the lower
  left corner

the room is empty of characters and people, no animals, no text, no letters,
no numbers, no labels, no posters with writing, no clutter on the floor,
not isometric, not pixel art, not 3D render, not photorealistic, no hard
cel-shading --ar 3:2
```

## 가구 좌표 검수표 (= `roomLayout.ts` 핫스팟 · ±4%는 코드에서 조정)

생성 후 반투명 사각형을 얹어 확인. 좌표는 방 전체의 %(좌상단 0,0).

| 가구 | 코드 ID | x, y (좌상단) | w × h | 비고 |
|---|---|---|---|---|
| 책장 | `documents` | 4, 8 | 12 × 44 | 벽에 붙어 바닥까지 |
| 책상 + 의자 | `tracker` | 20, 38 | 18 × 22 | 의자는 책상 아래 25,60 / 8×8. **미니미가 의자 자리(29,66)에 앉음** |
| 창문 | (장식) | 40, 6 | 16 × 24 | 뒷벽 중앙 |
| 게시판 | `jobs` | 60, 8 | 20 × 22 | 뒷벽 우측 |
| 침대 | `rest` | 80, 38 | 18 × 26 | 우측 벽 |
| 소파 | `mental` | 58, 66 | 22 × 20 | 설이(멘탈 케어)가 앉음(69,76 발 위치) |
| 러그 | (장식) | 28, 70 | 30 × 24 | 미니미 시작 위치(40,88) |
| 식물 | (장식) | 88,16 / 2,78 | 8×20 / 8×18 | |

**뒷벽/바닥 경계 = y 34%.** 캐릭터가 서는 바닥은 y 44~96%. 이 띠에 가구를 놓지 말 것(NPC 구담 48,58 · 설이 69,76 · 까론 88,89 · 미니미 이동 경로).

## 검수 기준

1. 3:2, 캐릭터·사람·동물 0, 글자 0 (게시판 메모는 빈 색지)
2. 가구 8종이 검수표 사각형 안에 들어오는가 (±4%)
3. 132px 폭으로 축소해도 가구 실루엣이 구분되는가 (모바일 폭 기준)
4. 팔레트: 보라·원색 금지, 채도는 saju 마을 히어로와 같은 톤
5. 바닥 y 44~96% 띠에 캐릭터를 가릴 만한 물건이 없는가

## 반입

`public/room/bg.jpg` 배치 → `/spike` 미리보기의 "배경 그림 사용" 토글로 좌표 확인 → 어긋난 핫스팟은 `roomLayout.ts` 숫자만 수정. 코드 폴백은 그대로 남겨 그림 로드 실패 시 fallback.

## 후속 슬롯 (지금은 제작하지 않음)

| 에셋 | 용도 |
|---|---|
| `room/desk-lit.png` (책상 영역 컷아웃) | D-day 신호 시 램프 켜진 책상으로 교체 — 현재는 코드 글로우 |
| `room/celebration.png` (꽃·풍선 오버레이) | 최종합격 연출 |
| 에이전트 소품 오버레이(안경·화분·커피) | 4 말랑이 개성 — saju B1 소품 오버레이와 같은 상단 앵커 규격 |
| 밤 버전 `room/bg-night.jpg` | 늦은 시간 접속 시 톤 전환 |
