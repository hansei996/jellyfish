"""把一只水母的一生做成一张 SVG 卡片 —— 不用浏览器就能发出去的「截图」。

为什么是 SVG 而不是 PNG：零依赖。生成一个矢量图不需要 Chrome、不需要 Pillow，
GitHub README 和浏览器都能直接渲染，贴到聊天工具里也是图。

卡片内容：伞盖（随临终体力缩放）、名字、活了多少天、死因、体力曲线、日志尾哈希。
"""
from __future__ import annotations

from xml.sax.saxutils import escape

W, H = 1200, 630


def _sparkline(timeline, x, y, width, height):
    """体力随时间的折线。没有数据就返回空串。"""
    energies = [p["energy"] for p in timeline if p.get("energy") is not None]
    if len(energies) < 2:
        return ""
    peak = max(max(energies), 1)
    step = width / (len(energies) - 1)
    points = []
    for index, value in enumerate(energies):
        px = x + index * step
        py = y + height - (value / peak) * height
        points.append("%.1f,%.1f" % (px, py))
    return (
        '<polyline fill="none" stroke="#3ec6d8" stroke-width="3" stroke-linejoin="round" '
        'points="' + " ".join(points) + '"/>'
    )


def build(life) -> str:
    state = life.state()
    timeline = life.timeline()
    alive = state["alive"]
    last_energy = state["energy"]
    peak = max(max([p["energy"] for p in timeline] or [1]), 1)
    scale = 0.45 + 0.55 * (last_energy / peak if peak else 0)
    rx = 150 * scale
    ry = rx * 0.78
    tent_color = "#63d6e6" if alive else "#9fb0bd"
    bell = "#7fe0ee" if alive else "#c3ccd4"
    title = escape(str(life.name))
    bio = escape(life.biography())
    tail = escape((life.records()[-1]["hash"][:16] if life.records() else "-"))
    status = "活着" if alive else "已死"
    spark = _sparkline(timeline, 120, 430, W - 240, 90)

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="' + str(W) + '" height="' + str(H) + '" '
        'viewBox="0 0 ' + str(W) + " " + str(H) + '">'
        '<defs><radialGradient id="bg" cx="50%" cy="18%" r="85%">'
        '<stop offset="0%" stop-color="#eaf7fb"/><stop offset="70%" stop-color="#ffffff"/>'
        "</radialGradient>"
        '<radialGradient id="bell" cx="50%" cy="38%" r="62%">'
        '<stop offset="0%" stop-color="#c9f2f9"/><stop offset="100%" stop-color="' + bell + '"/>'
        "</radialGradient></defs>"
        '<rect width="100%" height="100%" fill="url(#bg)"/>'
        # 水母
        '<g transform="translate(' + str(W // 2) + ',210)">'
        '<ellipse cx="0" cy="0" rx="' + "%.1f" % rx + '" ry="' + "%.1f" % ry + '" fill="url(#bell)"/>'
        '<g stroke="' + tent_color + '" stroke-width="4" fill="none" stroke-linecap="round" opacity="0.85">'
        '<path d="M-60 60 q-10 46 8 84"/><path d="M-20 74 q-8 54 4 96"/>'
        '<path d="M20 74 q8 54 -4 96"/><path d="M60 60 q10 46 -8 84"/>'
        "</g></g>"
        # 文字
        '<text x="' + str(W // 2) + '" y="86" text-anchor="middle" font-family="Segoe UI,Microsoft YaHei,sans-serif"'
        ' font-size="44" font-weight="650" fill="#0b1b2b">' + title + " 的一生</text>"
        '<text x="' + str(W // 2) + '" y="360" text-anchor="middle" font-family="Segoe UI,Microsoft YaHei,sans-serif"'
        ' font-size="26" fill="' + ("#1f7a3d" if alive else "#9b2c2c") + '">' + status + "</text>"
        '<text x="' + str(W // 2) + '" y="404" text-anchor="middle" font-family="Segoe UI,Microsoft YaHei,sans-serif"'
        ' font-size="22" fill="#24455f">' + bio + "</text>"
        # 体力曲线
        '<text x="120" y="424" font-family="ui-monospace,Consolas,monospace" font-size="15" fill="#5b7288">体力</text>'
        + spark +
        '<text x="120" y="562" font-family="ui-monospace,Consolas,monospace" font-size="14" fill="#7c8b99">'
        "日志尾哈希 " + tail + " · 每一 tick 都可重算</text>"
        '<text x="' + str(W - 120) + '" y="562" text-anchor="end" font-family="ui-monospace,Consolas,monospace"'
        ' font-size="14" fill="#7c8b99">jellyfish</text>'
        "</svg>"
    )


def write(life, out="card.svg") -> str:
    from pathlib import Path

    path = Path(out)
    path.write_text(build(life), encoding="utf-8")
    return str(path)
