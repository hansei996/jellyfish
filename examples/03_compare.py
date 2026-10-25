#!/usr/bin/env python3
"""例 3：横向比较 —— 同一批种子，五种活法各活多久。

    python examples/03_compare.py
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jellyfish.textio import force_utf8  # noqa: E402

force_utf8()

from jellyfish.core import POLICIES, default_world, initial_state, step  # noqa: E402


def gambler(state, world, roll):
    if not state["alive"]:
        return {"action": "none", "reason": "死了"}
    if state["energy"] <= 1 and world.get("food"):
        return {"action": "eat", "reason": "赌徒：不成就没命了"}
    if world.get("food") and roll < 0.15:
        return {"action": "eat", "reason": "赌徒：手气到了"}
    return {"action": "move", "reason": "赌徒：下一格更好"}


def life_days(policy, seed, limit=200):
    state = initial_state(seed)
    for _ in range(limit):
        world = default_world(state["tick"], seed)
        roll = ((state["tick"] * 2654435761 + seed) % 1000) / 1000.0
        state, _ = step(state, world, roll, policy)
        if not state["alive"]:
            break
    return state["tick"], state["eaten"], state["moved"]


def main() -> int:
    rows = [(name, name) for name in POLICIES] + [("gambler(自定义)", gambler)]
    print("%-18s %-10s %-10s %s" % ("活法", "中位寿命", "最短/最长", "平均 吃/走"))
    print("-" * 58)
    for label, policy in rows:
        lives = [life_days(policy, seed) for seed in range(40)]
        days = [x[0] for x in lives]
        eats = statistics.mean([x[1] for x in lives])
        moves = statistics.mean([x[2] for x in lives])
        print("%-18s %-10.0f %-10s %.1f / %.1f"
              % (label, statistics.median(days), "%d/%d" % (min(days), max(days)), eats, moves))
    print()
    print("注意：自定义的 gambler 只需要一个纯函数，不需要改库。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())