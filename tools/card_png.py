#!/usr/bin/env python3
"""card_png —— 把一只水母的一生画成 PNG（B站动态/朋友圈能直接上传的格式）。

为什么要有 PNG：SVG 浏览器能看，但社交平台不收。B站动态、微信都只认 jpg/png。
这张图用 Pillow 画，样式与 card.svg 一致（伞盖按临终体力缩放、体力曲线、日志尾哈希）。

    python tools/card_png.py --root card-life --out docs/example-card.png
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from jellyfish.log import Life  # noqa: E402

W, H = 1200, 630
FONT_CANDIDATES = (
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
)


def _font(size):
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _force_utf8():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def draw(life, out="card.png"):
    state = life.state()
    timeline = life.timeline()
    energies = [p["energy"] for p in timeline] or [1]
    peak = max(max(energies), 1)

    image = Image.new("RGB", (W, H), "#ffffff")
    d = ImageDraw.Draw(image)
    for y in range(0, H):
        t = y / (H - 1)
        top = (232, 247, 251)
        bottom = (255, 255, 255)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=color)

    # 水母
    cx, cy = W // 2, 200
    rx = int(55 + 60 * (state["energy"] / peak))
    ry = int(rx * 0.78)
    alive = state["alive"]
    bell = "#7fe0ee" if alive else "#c3ccd4"
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=bell)
    tent = "#63d6e6" if alive else "#9fb0bd"
    for dx, bend in ((-70, -12), (-24, -4), (24, 4), (70, 12)):
        d.line([(cx + dx * 0.8, cy + ry - 8), (cx + dx * 0.8 + bend, cy + ry + 56)], fill=tent, width=4)

    # 标题与传记
    d.text((W // 2, 52), "%s 的一生" % life.name, font=_font(44), fill="#0b1b2b", anchor="mm")
    d.text((W // 2, 108), "活着" if alive else "已死", font=_font(24),
           fill="#1f7a3d" if alive else "#9b2c2c", anchor="mm")
    d.text((W // 2, 400), life.biography(), font=_font(22), fill="#24455f", anchor="mm")

    # 体力曲线
    left, top, width, height = 140, 468, W - 280, 78
    points = []
    for index, value in enumerate(energies):
        px = left + width * index / max(len(energies) - 1, 1)
        py = top + height - height * (value / peak)
        points.append((px, py))
    if len(points) >= 2:
        d.line(points, fill="#3ec6d8", width=3)
    d.text((left, top - 22), "体力", font=_font(15), fill="#5b7288")

    records = life.records()
    tail = records[-1]["hash"][:16] if records else "-"
    d.text((left, 592), "日志尾哈希 %s · 每一 tick 都可重算" % tail, font=_font(15), fill="#7c8b99")
    d.text((W - 140, 592), "jellyfish", font=_font(15), fill="#7c8b99", anchor="ra")

    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")
    return str(path)


def main(argv):
    root = argv[argv.index("--root") + 1] if "--root" in argv else ".life"
    out = argv[argv.index("--out") + 1] if "--out" in argv else "card.png"
    name = argv[argv.index("--name") + 1] if "--name" in argv else "小水母"
    policy = argv[argv.index("--policy") + 1] if "--policy" in argv else "opportunist"
    print("已生成 " + draw(Life(root, name=name, policy=policy), out))
    return 0


if __name__ == "__main__":
    _force_utf8()
    sys.exit(main(sys.argv[1:]))