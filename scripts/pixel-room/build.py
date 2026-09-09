"""픽셀 방 에셋 빌드 — frontend/public/room/pixel/ 를 재생성한다.

    python scripts/pixel-room/build.py            # Kenney 팩을 .cache/ 에 내려받아 bg.png + 슬라임 5종 생성
    python scripts/pixel-room/build.py --preview  # 4배 확대 미리보기(scripts/pixel-room/preview.png)도 저장

에셋(전부 CC0, Kenney): Roguelike RPG(바닥·벽·창·문) · Roguelike Indoors(가구) · Tiny Dungeon(비교용 슬라임).
방 레이아웃(11×8 타일)은 frontend/src/components/room/roomLayout.ts 의 PIXEL_THEME 좌표와 1:1 — 여기서 타일을 옮기면 거기 %좌표도 함께 고친다.
의존성: Pillow (pip install pillow).
"""
from __future__ import annotations

import colorsys
import io
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "room" / "pixel"
CACHE = Path(__file__).resolve().parent / ".cache"
T, M = 16, 1          # 타일 16px + 1px 마진(Kenney 규격)
COLS, ROWS, WALL = 11, 8, 2

PACKS = {
    "rpg": ("roguelike-rpg-pack", "Spritesheet/roguelikeSheet_transparent.png"),
    "indoor": ("roguelike-indoors", "Tilesheets/roguelikeIndoor_transparent.png"),
    "tiny": ("tiny-dungeon", "Tilemap/tilemap.png"),
}


def fetch_sheet(slug: str, inner: str) -> Image.Image:
    """kenney.nl 에셋 페이지에서 zip 링크를 찾아 캐시에 받고 시트를 연다."""
    CACHE.mkdir(parents=True, exist_ok=True)
    zpath = CACHE / f"{slug}.zip"
    if not zpath.exists():
        html = urllib.request.urlopen(f"https://kenney.nl/assets/{slug}", timeout=30).read().decode("utf-8", "ignore")
        m = re.search(r'https?://[^"\' ]+\.zip', html)
        if not m:
            sys.exit(f"zip 링크를 찾지 못함: {slug}")
        zpath.write_bytes(urllib.request.urlopen(m.group(0), timeout=120).read())
    with zipfile.ZipFile(zpath) as z:
        name = next(n for n in z.namelist() if n.endswith(inner))
        return Image.open(io.BytesIO(z.read(name))).convert("RGBA")


def tile(sheet: Image.Image, c: int, r: int) -> Image.Image:
    return sheet.crop((c * (T + M), r * (T + M), c * (T + M) + T, r * (T + M) + T))


# ---------------------------------------------------------------- 방 배경
def build_background(rpg: Image.Image, ind: Image.Image) -> Image.Image:
    bg = Image.new("RGBA", (COLS * T, ROWS * T), (0, 0, 0, 0))

    def put(sheet, c, r, x, y):
        bg.alpha_composite(tile(sheet, c, r), (x * T, y * T))

    for y in range(ROWS):
        for x in range(COLS):
            if y < WALL:
                put(rpg, 14, 12, x, y) if y == 0 else put(rpg, 13, 15, x, y)   # 크림 벽(윗줄 어두운 띠 / 굽도리)
            else:
                put(rpg, 8, 2, x, y)                                             # 가로 나무 판자
    # 뒷벽 장식
    for s, c, r, x, y in [
        (ind, 16, 12, 1, 0),                                  # 작은 그림
        (rpg, 45, 2, 3, 0), (rpg, 45, 3, 3, 1),               # 아치 창문
        (rpg, 54, 4, 5, 1),                                   # 문
        (ind, 20, 12, 7, 0), (ind, 21, 12, 8, 0), (ind, 20, 13, 7, 1), (ind, 21, 13, 8, 1),   # 게시판 2×2
        (ind, 22, 14, 10, 0), (ind, 22, 15, 10, 1),           # 거울
    ]:
        put(s, c, r, x, y)
    # 초록 러그 3×3
    for ry in range(3):
        for rx in range(3):
            put(ind, 7 + rx, 9 + ry, 4 + rx, 4 + ry)
    # 가구
    for s, c, r, x, y in [
        (ind, 4, 17, 0, 2), (ind, 7, 17, 1, 2),                                   # 서류·파일 선반 (📚)
        (ind, 0, 0, 2, 2), (ind, 2, 0, 3, 2), (ind, 0, 1, 2, 3), (ind, 2, 1, 3, 3),   # 책상 2×2 (📝)
        (ind, 1, 2, 2, 4),                                                        # 의자(앉는 자리)
        (ind, 9, 0, 10, 2), (ind, 9, 1, 10, 3),                                   # 침대 (💤)
        (ind, 23, 15, 8, 5), (ind, 24, 15, 9, 5), (ind, 23, 16, 8, 6), (ind, 24, 16, 9, 6),   # 초록 소파 2×2 (🌿)
        (ind, 6, 2, 6, 2), (ind, 6, 3, 6, 3),                                     # 원형 티테이블
        (ind, 16, 0, 0, 7), (ind, 17, 0, 10, 7),                                  # 식물
    ]:
        put(s, c, r, x, y)
    return bg


# ---------------------------------------------------------------- 슬라임(블롭) — 방 팔레트로 직접 그림
OUTLINE = (90, 70, 52, 255)
EYE = (60, 45, 40, 255)
PALETTE = {
    "me": (242, 226, 196, 255),        # 크림
    "seo_yeon": (229, 154, 134, 255),  # 코랄
    "jun_ho": (143, 179, 217, 255),    # 파랑
    "ha_eun": (158, 201, 143, 255),    # 세이지
    "min_su": (240, 208, 120, 255),    # 버터
}


def lighten(c, f):
    return tuple(min(255, int(v + (255 - v) * f)) for v in c[:3]) + (255,)


def darken(c, f):
    return tuple(int(v * (1 - f)) for v in c[:3]) + (255,)


def draw_blob(body, blush=(232, 150, 140, 255)) -> Image.Image:
    im = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    px = im.load()
    rows = {4: (7, 8), 5: (5, 10), 6: (4, 11), 7: (3, 12), 8: (3, 12), 9: (2, 13), 10: (2, 13), 11: (2, 13), 12: (2, 13), 13: (3, 12), 14: (4, 11)}
    body_set = {(x, y) for y, (x0, x1) in rows.items() for x in range(x0, x1 + 1)}
    for x, y in body_set:
        px[x, y] = body
    for x, y in body_set:                                   # 외곽선
        if any((x + dx, y + dy) not in body_set for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            px[x, y] = OUTLINE
    for x in range(5, 11):                                  # 바닥 그림자
        if px[x, 14] != OUTLINE:
            px[x, 14] = darken(body, 0.18)
    hl = lighten(body, 0.55)
    for x, y in [(5, 6), (6, 6), (5, 7), (4, 8), (6, 5)]:   # 하이라이트
        px[x, y] = hl
    for x, y in [(6, 9), (6, 10), (10, 9), (10, 10)]:       # 눈
        px[x, y] = EYE
    px[7, 9] = (255, 255, 255, 255)
    px[11, 9] = (255, 255, 255, 255)
    px[4, 11] = blush
    px[12, 11] = blush
    px[8, 12] = darken(body, 0.35)                          # 입
    px[14, 13] = body                                       # 물방울
    return im


def recolor(im: Image.Image, hue=None, sat=None, light=None) -> Image.Image:
    """Tiny Dungeon 슬라임 색상 회전(비교용). 어두운 외곽선·눈은 유지."""
    out = Image.new("RGBA", im.size)
    for x in range(im.width):
        for y in range(im.height):
            r, g, b, a = im.getpixel((x, y))
            if a == 0:
                out.putpixel((x, y), (0, 0, 0, 0))
                continue
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if l < 0.25:
                out.putpixel((x, y), (r, g, b, a))
                continue
            h = hue if hue is not None else h
            s = sat if sat is not None else s
            l = min(1, l * light) if light is not None else l
            R, G, B = colorsys.hls_to_rgb(h, l, s)
            out.putpixel((x, y), (int(R * 255), int(G * 255), int(B * 255), a))
    return out


def main() -> None:
    preview = "--preview" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    rpg = fetch_sheet(*PACKS["rpg"])
    ind = fetch_sheet(*PACKS["indoor"])
    tiny = fetch_sheet(*PACKS["tiny"])

    bg = build_background(rpg, ind)
    bg.save(OUT / "bg.png", optimize=True)

    for key, color in PALETTE.items():
        draw_blob(color).save(OUT / f"blob_{key}.png")

    slime = tile(tiny, 0, 9)
    variants = {
        "me": recolor(slime, hue=0.10, sat=0.55, light=1.25),
        "seo_yeon": recolor(slime, hue=0.98, sat=0.65),
        "jun_ho": recolor(slime, hue=0.58, sat=0.65),
        "ha_eun": slime,
        "min_su": recolor(slime, hue=0.13, sat=0.85),
    }
    for key, im in variants.items():
        im.save(OUT / f"slime_{key}.png")

    (OUT / "LICENSE-kenney.txt").write_text(
        "bg.png · slime_*.png — Kenney Roguelike RPG / Roguelike Indoors / Tiny Dungeon, CC0 1.0 (https://kenney.nl)\n"
        "blob_*.png — 이 저장소에서 그림 (scripts/pixel-room/build.py)\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT} ({len(list(OUT.iterdir()))} files)")

    if preview:
        S = 4
        room = bg.copy()
        for key, (tx, ty) in {"jun_ho": (5.5, 3.5), "ha_eun": (8.5, 5.4), "min_su": (6.5, 7.5), "me": (5.5, 5.6)}.items():
            room.alpha_composite(Image.open(OUT / f"blob_{key}.png"), (int(tx * T - 8), int(ty * T - 15)))
        pv = room.resize((room.width * S, room.height * S), Image.NEAREST)
        ImageDraw.Draw(pv).text((6, 6), "pixel room preview", fill=(255, 255, 255, 255))
        pv.save(Path(__file__).resolve().parent / "preview.png")
        print("preview.png saved")


if __name__ == "__main__":
    main()
