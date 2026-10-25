#!/usr/bin/env python3
"""例 1：换掉「它看到什么」—— 用一串伪天气当世界。

    python examples/01_custom_world.py

这个例子只改 default_world，不碰策略：雨天没吃的，晴天有。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jellyfish.core import initial_state, step  # noqa: E402


def weather_world(tick: int, seed: int = 0) -> dict:
    """0=雨 1=多云 2=晴。晴天才长吃的。"""
    kind = (tick * 5 + seed * 7) % 3
    return {"weather": kind, "food": 1 if kind == 2 else 0}


def main() -> int:
    print("%-5s %-6s %-5s %-5s %s" % ("tick", "天气", "食物", "决定", "体力"))
    state = initial_state(0)
    for _ in range(12):
        world = weather_world(state["tick"], 0)
        roll = ((state["tick"] * 2654435761) % 1000) / 1000.0
        before = state["energy"]
        state, record = step(state, world, roll, "balanced")
        print("%-5d %-6s %-5d %-5s %d→%d" % (
            state["tick"], ["雨", "多云", "晴"][world["weather"]], world["food"],
            record["decision"]["action"], before, state["energy"]))
        if not state["alive"]:
            print("第 %d 天饿死。" % state["tick"])
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
