#!/usr/bin/env python3
"""jellyfish —— 养一只会死的水母。单文件版，零依赖。

    python jellyfish.py serve         # http://127.0.0.1:8080
    python jellyfish.py tick --times 30 --name 小水母
    python jellyfish.py state
    python jellyfish.py export --out life.html

这是从 jellyfish/ 包自动生成的（tools/build_single.py），不要直接改这个文件。
"""

# ----------------------------------------------------------------------
# 来自 jellyfish/textio.py
# ----------------------------------------------------------------------

import sys


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


# ----------------------------------------------------------------------
# 来自 jellyfish/core.py
# ----------------------------------------------------------------------

import hashlib
import json

EAT_GAIN = 2
MOVE_COST = 2
IDLE_COST = 1
START_ENERGY = 5
MAX_ENERGY = 8


def canon(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value) -> str:
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def initial_state(seed: int = 0) -> dict:
    return {
        "tick": 0,
        "energy": START_ENERGY,
        "alive": True,
        "death_reason": None,
        "seed": seed,
        "eaten": 0,
        "moved": 0,
    }


def default_world(tick: int, seed: int = 0) -> dict:
    """默认世界：食物是稀缺的，且随天数变化 —— 所以它真可能饿死。"""
    # 注意：乘数不能等于模数，否则 (tick*7) % 7 恒为 0，食物永远是常数（这个 bug 真的发生过）
    return {"food": 1 if ((tick * 3 + seed * 13) % 7) in (0, 1) else 0}


POLICIES = ("balanced", "frugal", "adventurous", "opportunist")


def decide_with(state: dict, world: dict, roll: float, policy: str = "balanced") -> dict:
    """不同性格的水母，同一个世界。policy 决定它怎么权衡吃与走。"""
    if not state["alive"]:
        return {"action": "none", "reason": "已经死了，什么也做不了"}

    food_here = world.get("food", 0)
    energy = state["energy"]

    if policy == "frugal":
        # 节能型：只在很饿的时候才动，能蹭就蹭
        if energy <= 2 and food_here > 0:
            return {"action": "eat", "reason": "节能型：没能量了，眼前有吃的"}
        if energy <= 2:
            return {"action": "move", "reason": "节能型：快饿死了才肯走一趟"}
        if food_here > 0 and roll < 0.5:
            return {"action": "eat", "reason": "节能型：有吃的就顺手吃一口"}
        return {"action": "idle", "reason": "节能型：不动最省能量"}

    if policy == "adventurous":
        # 冒险型：宁可多走，去赌下一格有吃的；但饿到 3 以下会先吃
        if energy <= 3 and food_here > 0:
            return {"action": "eat", "reason": "冒险型：快没劲了，有吃的先吃"}
        if food_here > 0 and roll < 0.5:
            return {"action": "eat", "reason": "冒险型：顺手吃一口再走"}
        return {"action": "move", "reason": "冒险型：待着太无聊，去找更多"}

    if policy == "opportunist":
        # 投机型：能量低于中位线就囤，够吃就停
        if energy <= 3 and food_here > 0:
            return {"action": "eat", "reason": "投机型：低位补仓"}
        if energy <= 3:
            return {"action": "move", "reason": "投机型：低位没货，去找"}
        if food_here > 0 and energy <= MAX_ENERGY - EAT_GAIN:
            return {"action": "eat", "reason": "投机型：能囤就囤，别等涨"}
        return {"action": "idle", "reason": "投机型：仓位够了，观望"}

    # balanced：默认
    if energy <= 2:
        if food_here > 0:
            return {"action": "eat", "reason": "能量 %d 快见底，眼前有食物" % energy}
        return {"action": "move", "reason": "能量 %d 快见底，这里没吃的，得走" % energy}
    if energy >= MAX_ENERGY - 1:
        return {"action": "idle", "reason": "能量充足，先待着"}
    if food_here > 0 and roll < 0.9:
        return {"action": "eat", "reason": "有食物，吃的收益比探索大"}
    if roll < 0.5:
        return {"action": "move", "reason": "想换个地方看看有没有吃的"}
    return {"action": "idle", "reason": "暂时不动"}


def decide(state: dict, world: dict, roll: float) -> dict:
    """这一 tick 想做什么。纯函数，只依赖 (状态, 世界, 随机值)。"""
    if not state["alive"]:
        return {"action": "none", "reason": "已经死了，什么也做不了"}

    food_here = world.get("food", 0)
    if state["energy"] <= 2:
        if food_here > 0:
            return {"action": "eat", "reason": "能量 %d 快见底，眼前有食物" % state["energy"]}
        return {"action": "move", "reason": "能量 %d 快见底，这里没吃的，得走" % state["energy"]}

    if state["energy"] >= MAX_ENERGY - 1:
        return {"action": "idle", "reason": "能量充足，先待着"}

    if food_here > 0 and roll < 0.7:
        return {"action": "eat", "reason": "有食物，吃的收益比探索大"}
    if roll < 0.5:
        return {"action": "move", "reason": "想换个地方看看有没有吃的"}
    return {"action": "idle", "reason": "暂时不动"}


def step(state: dict, world: dict, roll: float, policy="balanced") -> tuple[dict, dict]:
    """返回 (新状态, 这一步的记录)。纯函数。

    policy 可以是内置名字（字符串），也可以是一个自定义函数：
        decide(state, world, roll) -> {"action": ..., "reason": ...}
    这让"换一种活法"不需要改库，只要传一个函数。
    """
    if callable(policy):
        decision = policy(state, world, roll)
    else:
        decision = decide_with(state, world, roll, policy)
    new = json.loads(json.dumps(state))
    new["tick"] += 1

    action = decision["action"]
    if action == "eat":
        new["energy"] = min(MAX_ENERGY, new["energy"] + EAT_GAIN)
        new["eaten"] += 1
    elif action == "move":
        new["energy"] -= MOVE_COST
        new["moved"] += 1
    elif action == "idle":
        new["energy"] -= IDLE_COST
    # action == "none"：死人不动，也不掉能量

    if new["alive"] and new["energy"] <= 0:
        new["energy"] = 0
        new["alive"] = False
        new["death_reason"] = "饿死：第 %d 个 tick 能量归零" % new["tick"]

    record = {
        "tick": new["tick"],
        "world": world,
        "roll": roll,
        "decision": decision,
        "state": new,
        "state_hash": digest(new),
    }
    return new, record


def revive(state: dict, energy: int = START_ENERGY) -> dict:
    """复活：不是把状态改回去，而是开一段新的生命（tick 继续，历史保留）。"""
    new = json.loads(json.dumps(state))
    new["alive"] = True
    new["death_reason"] = None
    new["energy"] = energy
    new["tick"] += 1
    return new


# ----------------------------------------------------------------------
# 来自 jellyfish/log.py
# ----------------------------------------------------------------------

import json
from pathlib import Path

LOG_NAME = "life.jsonl"


class Life:
    def __init__(self, root=".life", seed=0, name="小水母", policy="balanced"):
        self.root = Path(root)
        self.path = self.root / LOG_NAME
        self.seed = seed
        self.name = name
        self.policy = policy
        self._state = None
        self._records = None

    # -- 读日志 ---------------------------------------------------------
    def records(self):
        if self._records is None:
            out = []
            prev = None
            if self.path.exists():
                for lineno, line in enumerate(self.path.read_text(encoding="utf-8-sig").splitlines(), 1):
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    if record.get("prev") != prev:
                        raise ValueError("第 %d 条记录链断了" % lineno)
                    if record.get("hash") != self._hash(record):
                        raise ValueError("第 %d 条记录被改过" % lineno)
                    prev = record["hash"]
                    out.append(record)
            self._records = out
        return self._records

    @staticmethod
    def _hash(record):
        body = {k: v for k, v in record.items() if k != "hash"}
        return digest(body)

    # -- 状态 -----------------------------------------------------------
    def state(self):
        if self._state is None:
            state = initial_state(self.seed)
            for record in self.records():
                if record["kind"] == "tick":
                    state, _ = step(state, record["world"], record["roll"], self.policy)
                elif record["kind"] == "revive":
                    state = revive(state)
            self._state = state
        return self._state

    def state_at(self, tick: int):
        state = initial_state(self.seed)
        for record in self.records():
            if record["kind"] == "tick":
                state, _ = step(state, record["world"], record["roll"])
                if state["tick"] >= tick:
                    break
            elif record["kind"] == "revive":
                state = revive(state)
        return state

    # -- 写 -------------------------------------------------------------
    def _append(self, record):
        record = dict(record)
        records = self.records()
        record["prev"] = records[-1]["hash"] if records else None
        record["hash"] = self._hash(record)
        self.root.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canon(record) + chr(10))
        self._records = records + [record]
        self._state = None
        return record

    def tick(self, world=None, roll=None):
        state = self.state()
        # 默认世界不是"每天都有吃的"：食物按 tick 变化，所以它真的可能饿死
        world = world if world is not None else default_world(state["tick"], self.seed)
        if roll is None:
            roll = ((state["tick"] * 2654435761 + self.seed) % 1000) / 1000.0
        new, _ = step(state, world, roll, self.policy)
        record = self._append({"kind": "tick", "world": world, "roll": roll})
        self._state = new
        return record

    def do_revive(self):
        state = self.state()
        if state["alive"]:
            raise ValueError("它还活着，不需要复活")
        new = revive(state)
        record = self._append({"kind": "revive"})
        self._state = new
        return record

    def biography(self):
        """一句话说清它的一生 —— 这是要发出去的那句话。"""
        state = self.state()
        days = state["tick"]
        if state["alive"]:
            return "%s 已经活了 %d 天，吃了 %d 次，走了 %d 次。" % (self.name, days, state["eaten"], state["moved"])
        return "%s 活了 %d 天，第 %d 天饿死。它吃了 %d 次，走了 %d 次。" % (
            self.name, days, days, state["eaten"], state["moved"])

    def timeline(self):
        """给页面用：每一步的观测 → 决策 → 状态。"""
        out = []
        state = initial_state(self.seed)
        for record in self.records():
            if record["kind"] == "tick":
                state, step_record = step(state, record["world"], record["roll"])
                out.append({
                    "tick": step_record["tick"],
                    "world": step_record["world"],
                    "action": step_record["decision"]["action"],
                    "reason": step_record["decision"]["reason"],
                    "energy": state["energy"],
                    "alive": state["alive"],
                    "death_reason": state["death_reason"],
                    "state_hash": record["hash"][:12],
                })
            elif record["kind"] == "revive":
                state = revive(state)
                out.append({
                    "tick": state["tick"],
                    "world": {},
                    "action": "revive",
                    "reason": "被人复活",
                    "energy": state["energy"],
                    "alive": True,
                    "death_reason": None,
                    "state_hash": record["hash"][:12],
                })
        return out


# ----------------------------------------------------------------------
# 来自 jellyfish/export.py
# ----------------------------------------------------------------------

import json
from pathlib import Path


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_page(life, out="life.html") -> str:
    timeline = life.timeline()
    state = life.state()
    payload = json.dumps({"state": state, "timeline": timeline}, ensure_ascii=False)
    html = (
        "<!DOCTYPE html><html lang=zh-CN><head><meta charset=utf-8>"
        "<title>一个数字生命的一生</title>"
        "<style>body{font:15px/1.6 -apple-system,Segoe UI,Microsoft YaHei,sans-serif;margin:24px;color:#111}"
        "h1{font-size:20px}table{border-collapse:collapse;width:100%;font-size:13px}"
        "th,td{border-bottom:1px solid #eee;padding:6px 8px;text-align:left;vertical-align:top}"
        "th{color:#777}tr.dead td{color:#b3261e}code{background:#f3f3f3;padding:1px 5px;border-radius:4px}"
        ".big{font-size:32px;font-weight:700}.card{background:#f6f6f6;border-radius:10px;padding:14px 18px;font-size:17px;line-height:1.7}</style></head><body>"
        "<h1>" + _esc(life.name) + " 的一生</h1>"
        "<p class=card>" + _esc(life.biography()) + "</p>"
        "<p class=big id=energy></p><p id=meta class=sub></p><p id=death></p>"
        "<table><thead><tr><th>tick</th><th>看到什么</th><th>决定</th><th>为什么</th><th>能量</th><th>状态</th></tr></thead>"
        "<tbody id=rows></tbody></table>"
        "<script>var DATA=" + payload + ";"
        "var s=DATA.state;document.getElementById('energy').textContent=s.energy+' 能量';"
        "document.getElementById('meta').textContent='第 '+s.tick+' 天 · 吃过 '+s.eaten+' 次 · 走过 '+s.moved+' 次';"
        "if(!s.alive){document.getElementById('death').textContent='死因：'+s.death_reason;}"
        "document.getElementById('rows').innerHTML=DATA.timeline.map(function(r){return '<tr class=\"'+(r.alive?'':'dead')+'\"><td>'+r.tick+'</td><td>食物 '+((r.world||{}).food)+'</td><td><code>'+r.action+'</code></td><td>'+r.reason+'</td><td>'+r.energy+'</td><td>'+(r.alive?'活着':(r.death_reason||'死了'))+'</td></tr>';}).join('');"
        "</script></body></html>"
    )
    path = Path(out)
    path.write_text(html, encoding="utf-8")
    return str(path)


# ----------------------------------------------------------------------
# 来自 jellyfish/card.py
# ----------------------------------------------------------------------

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


# ----------------------------------------------------------------------
# 来自 jellyfish/movie.py
# ----------------------------------------------------------------------

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


# ----------------------------------------------------------------------
# 来自 jellyfish/server.py
# ----------------------------------------------------------------------

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PAGE = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>一只水母</title>
<style>
:root{--ink:#0b1b2b;--dim:#5b7288;--line:#dce7f0;--glow:#3ec6d8;--dead:#98a6b3}
*{box-sizing:border-box}
body{margin:0;font:15px/1.6 -apple-system,Segoe UI,Microsoft YaHei,sans-serif;color:var(--ink);
background:radial-gradient(120% 80% at 50% 0%,#eaf7fb 0%,#f7fbfd 55%,#ffffff 100%);min-height:100vh}
.wrap{max-width:860px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:19px;margin:0 0 2px;font-weight:650}
.sub{color:var(--dim);font-size:13px;margin:0}
.stage{position:relative;height:320px;margin:18px 0 6px;display:flex;align-items:center;justify-content:center;overflow:hidden}
#jelly{transition:opacity .8s, transform .8s}
.dead #jelly{opacity:.28;transform:translateY(26px) scale(.86)}
.bio{font-size:17px;line-height:1.7;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin:0 0 14px}
.bio.dead{border-color:#f0c9c9;background:#fff7f7;color:#9b2c2c}
.row{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 18px}
button{font:inherit;padding:9px 16px;border-radius:10px;border:1px solid #c9d8e4;background:#fff;cursor:pointer}
button:hover{background:#f1f8fb}
button.primary{background:#0b1b2b;color:#fff;border-color:#0b1b2b}
table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--dim);font-weight:600;background:#fbfdff}
tr.dead td{color:#9b2c2c}
code{font-family:ui-monospace,Consolas,monospace;font-size:12px;background:#eef4f8;padding:1px 5px;border-radius:4px}
.tick-n{color:var(--dim);font-variant-numeric:tabular-nums}
</style></head><body><div class="wrap">
<h1 id="title">一只水母</h1>
<p class="sub">它会饿、会死。每一步都写进 append-only 日志，可以倒回去重看。</p>

<div class="stage"><svg id="jelly" width="220" height="260" viewBox="0 0 220 260">
  <defs><radialGradient id="g" cx="50%" cy="40%" r="60%">
    <stop offset="0%" stop-color="#9fe8f3" stop-opacity=".95"/>
    <stop offset="100%" stop-color="#3ec6d8" stop-opacity=".75"/></radialGradient></defs>
  <ellipse id="bell" cx="110" cy="96" rx="66" ry="52" fill="url(#g)"/>
  <g id="tent" stroke="#63d6e6" stroke-width="3" fill="none" stroke-linecap="round" opacity=".85">
    <path d="M78 140 q-8 34 6 62"/><path d="M98 146 q-6 40 4 74"/>
    <path d="M122 146 q6 40 -4 74"/><path d="M142 140 q8 34 -6 62"/>
  </g>
</svg></div>

<p class="bio" id="bio">…</p>
<div class="row">
  <button class="primary" onclick="tick(1)">过一天</button>
  <button onclick="tick(5)">过五天</button>
  <button onclick="revive()">救活它</button>
</div>

<table><thead><tr><th>第几天</th><th>看到</th><th>决定</th><th>为什么</th><th>体力</th><th>状态</th></tr></thead>
<tbody id="rows"></tbody></table>
</div>
<script>
function render(d){
  var s=d.state, alive=s.alive, e=s.energy;
  document.body.classList.toggle('dead', !alive);
  document.getElementById('title').textContent = d.name || '一只水母';
  var bio=document.getElementById('bio');
  bio.textContent = d.biography;
  bio.classList.toggle('dead', !alive);
  var bell=document.getElementById('bell');
  var rx = 38 + Math.min(e,8)/8*34;
  bell.setAttribute('rx', rx.toFixed(1));
  bell.setAttribute('ry', (rx*0.78).toFixed(1));
  document.getElementById('tent').setAttribute('stroke', alive? '#63d6e6' : '#b9c4cd');
  var rows=d.timeline.slice().reverse().map(function(r){
    return '<tr class="'+(r.alive?'':'dead')+'"><td class=tick-n>'+r.tick+'</td><td>食物 '+((r.world||{}).food)+'</td>'+
      '<td><code>'+r.action+'</code></td><td>'+r.reason+'</td><td>'+r.energy+'</td>'+
      '<td>'+(r.alive?'活着':(r.death_reason||'死了'))+'</td></tr>';
  }).join('');
  document.getElementById('rows').innerHTML = rows || '<tr><td colspan=6 class=sub>还没有任何一天。点「过一天」。</td></tr>';
}
function load(){ fetch('/api/state').then(r=>r.json()).then(render); }
function tick(n){ fetch('/api/tick?n='+(n||1),{method:'POST'}).then(r=>r.json()).then(render); }
function revive(){ fetch('/api/revive',{method:'POST'}).then(r=>r.json()).then(render); }
load();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    life: Life = None

    def _send(self, code, body, content_type="application/json; charset=utf-8"):
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self):
        return json.dumps({"name": self.life.name, "biography": self.life.biography(),
                           "state": self.life.state(), "timeline": self.life.timeline()}, ensure_ascii=False)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if parsed.path == "/api/state":
            query = parse_qs(parsed.query)
            if "at" in query:
                state = self.life.state_at(int(query["at"][0]))
                return self._send(200, json.dumps({"state": state}, ensure_ascii=False))
            return self._send(200, self._json())
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tick":
            n = int((parse_qs(parsed.query).get("n") or ["1"])[0])
            for _ in range(max(1, min(n, 30))):
                if self.life.state()["alive"]:
                    self.life.tick()
                else:
                    break
            return self._send(200, self._json())
        if parsed.path == "/api/revive":
            try:
                self.life.do_revive()
            except ValueError as exc:
                return self._send(400, json.dumps({"error": str(exc)}, ensure_ascii=False))
            return self._send(200, self._json())
        return self._send(404, json.dumps({"error": "not found"}))

    def log_message(self, fmt, *args):
        pass


def serve(root=".life", host="127.0.0.1", port=8080):
    Handler.life = Life(root)
    httpd = ThreadingHTTPServer((host, port), Handler)
    print("数字生命在 http://%s:%d 活着（日志：%s）" % (host, port, Handler.life.path))
    print("Ctrl+C 结束；结束后它仍会在日志里等着被重看。")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("已停止。")
    finally:
        httpd.server_close()


# ----------------------------------------------------------------------
# 命令行
# ----------------------------------------------------------------------

write_movie = write
write_card = write
"""命令行：serve / tick / state / export"""

import json
import sys


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = ".life"
    name = "小水母"
    if "--root" in argv:
        root = argv[argv.index("--root") + 1]
    if "--name" in argv:
        name = argv[argv.index("--name") + 1]
    policy = argv[argv.index("--policy") + 1] if "--policy" in argv else "balanced"
    cmd = argv[0] if argv else "serve"

    if cmd == "serve":
        port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8080
        serve(root, port=port)
        return 0
    if cmd == "tick":
        life = Life(root, name=name, policy=policy)
        n = int(argv[argv.index("--times") + 1]) if "--times" in argv else 1
        for _ in range(n):
            if life.state()["alive"]:
                life.tick()
        state = life.state()
        print(json.dumps(state, ensure_ascii=False))
        return 0
    if cmd == "state":
        print(json.dumps(Life(root).state(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "movie":

        out = argv[argv.index("--out") + 1] if "--out" in argv else "life-movie.svg"
        print("已生成 " + write_movie(Life(root, name=name, policy=policy), out))
        return 0
    if cmd == "card":

        out = argv[argv.index("--out") + 1] if "--out" in argv else "card.svg"
        print("已生成 " + write_card(Life(root, name=name, policy=policy), out))
        return 0
    if cmd == "export":
        out = argv[argv.index("--out") + 1] if "--out" in argv else "life.html"
        print("已导出 " + write_page(Life(root), out))
        return 0
    print("用法：python -m jellyfish [serve|tick|state|export|card|movie] [--root .life] [--port 8080] [--name 名字] [--policy 性格]")
    return 2


if __name__ == "__main__":
    force_utf8()
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())
