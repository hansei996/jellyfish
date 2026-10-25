"""movie —— 把一生做成一个会动的 SVG（GIF 的零依赖替代）。

为什么不是 GIF：生成 GIF 要 Pillow/ffmpeg。SMIL/CSS 动画的 SVG 浏览器直接播，
GitHub README 也能显示，而且文件很小（几 KB）。

画面：伞盖随体力收缩、体力条变短、时间轴上的点往前走；最后一帧浮出死因。
"""
from __future__ import annotations

from xml.sax.saxutils import escape

W, H = 900, 560


def build(life, tick_seconds=0.45) -> str:
    timeline = life.timeline()
    if not timeline:
        raise ValueError("这只水母还没有任何一天，先 tick 几下")

    energies = [p["energy"] for p in timeline]
    peak = max(max(energies), 1)
    total = len(timeline) * tick_seconds
    death_at = total if life.state()["alive"] else (timeline[-1]["tick"]) * tick_seconds

    rx_values = ";".join("%.1f" % (40 + 60 * (e / peak)) for e in energies) or "40"
    bar_values = ";".join("%.1f" % (240 * (e / peak)) for e in energies) or "0"
    dot_values = ";".join("%.1f" % (40 + 520 * i / max(len(timeline) - 1, 1)) for i in range(len(timeline)))

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="' + str(W) + '" height="' + str(H) + '" '
        'viewBox="0 0 ' + str(W) + " " + str(H) + '">'
        '<defs><radialGradient id="bg" cx="50%" cy="20%" r="80%">'
        '<stop offset="0%" stop-color="#eaf7fb"/><stop offset="75%" stop-color="#ffffff"/>'
        "</radialGradient>"
        '<radialGradient id="bell" cx="50%" cy="38%" r="62%">'
        '<stop offset="0%" stop-color="#d6f7fc"/><stop offset="100%" stop-color="#7fe0ee"/>'
        "</radialGradient></defs>"
        '<rect width="100%" height="100%" fill="url(#bg)"/>'
        '<text x="' + str(W // 2) + '" y="64" text-anchor="middle" font-family="Segoe UI,Microsoft YaHei,sans-serif"'
        ' font-size="26" font-weight="650" fill="#0b1b2b">' + escape(str(life.name)) + " 的一生（播放中）</text>"

        # 水母：伞盖宽度随时间收缩
        '<g transform="translate(' + str(W // 2) + ',200)">'
        '<ellipse cx="0" cy="0" rx="100" ry="78" fill="url(#bell)">'
        '<animate attributeName="rx" values="' + rx_values + '" dur="' + "%.1f" % total + 's" repeatCount="indefinite"/>'
        '<animate attributeName="ry" values="' + ";".join("%.1f" % (float(v) * 0.78) for v in rx_values.split(";")) + '"'
        ' dur="' + "%.1f" % total + 's" repeatCount="indefinite"/></ellipse>'
        '<g stroke="#63d6e6" stroke-width="4" fill="none" stroke-linecap="round" opacity="0.85">'
        '<path d="M-56 58 q-10 40 6 74"><animate attributeName="d" '
        'values="M-56 58 q-14 40 6 74;M-56 58 q-2 40 -6 74;M-56 58 q-14 40 6 74" '
        'dur="2.4s" repeatCount="indefinite"/></path>'
        '<path d="M-18 72 q-8 46 2 84"><animate attributeName="d" '
        'values="M-18 72 q-2 46 6 84;M-18 72 q-14 46 -6 84;M-18 72 q-2 46 6 84" '
        'dur="2.9s" repeatCount="indefinite"/></path>'
        '<path d="M18 72 q8 46 -2 84"><animate attributeName="d" '
        'values="M18 72 q14 46 6 84;M18 72 q2 46 -6 84;M18 72 q14 46 6 84" '
        'dur="2.6s" repeatCount="indefinite"/></path>'
        '<path d="M56 58 q10 40 -6 74"><animate attributeName="d" '
        'values="M56 58 q2 40 6 74;M56 58 q14 40 -6 74;M56 58 q2 40 6 74" '
        'dur="3.1s" repeatCount="indefinite"/></path>'
        "</g></g>"

        # 体力条
        '<rect x="180" y="372" width="240" height="14" rx="7" fill="#e7f1f6"/>'
        '<rect x="180" y="372" width="240" height="14" rx="7" fill="#3ec6d8">'
        '<animate attributeName="width" values="' + bar_values + '" dur="' + "%.1f" % total + 's" repeatCount="indefinite"/>'
        "</rect>"
        '<text x="180" y="360" font-family="ui-monospace,Consolas,monospace" font-size="13" fill="#5b7288">体力</text>'

        # 时间轴
        '<line x1="40" y1="430" x2="560" y2="430" stroke="#cfe0ea" stroke-width="2"/>'
        '<circle cx="40" cy="430" r="7" fill="#0b1b2b">'
        '<animate attributeName="cx" values="' + dot_values + '" dur="' + "%.1f" % total + 's" repeatCount="indefinite"/>'
        "</circle>"
        '<text x="40" y="458" font-family="ui-monospace,Consolas,monospace" font-size="13" fill="#7c8b99">'
        "第 1 天 → 第 " + str(len(timeline)) + " 天</text>"

        # 结局：在死亡那一刻浮现
        '<text x="' + str(W - 40) + '" y="372" text-anchor="end" font-family="Segoe UI,Microsoft YaHei,sans-serif"'
        ' font-size="20" fill="#9b2c2c" opacity="0">' + escape(life.biography()) + "".join(
            '<animate attributeName="opacity" values="0;0;1" keyTimes="0;%.3f;%.3f" dur="' % (
                min(0.98, death_at / total), min(1.0, death_at / total + 0.02),
            ) + "%.1f" % total + 's" repeatCount="indefinite"/>'
        ) + "</text>"
        "</svg>"
    )


def write(life, out="life-movie.svg", tick_seconds=0.45) -> str:
    from pathlib import Path

    path = Path(out)
    path.write_text(build(life, tick_seconds), encoding="utf-8")
    return str(path)
