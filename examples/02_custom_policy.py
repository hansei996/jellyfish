#!/usr/bin/env python3
"""例 2：换掉「它怎么决定」—— 一只赌徒水母。

    python examples/02_custom_policy.py

自定义 policy 就是一个函数：(state, world, roll) -> {"action": ..., "reason": ...}
它仍然是纯函数，所以这只赌徒的一生同样可以被完整重放。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jellyfish.core import default_world, initial_state, step  # noqa: E402


def gambler(state: dict, world: dict, roll: float) -> dict:
    """只在 roll < 0.15 时吃（赌它之后还有更好的），否则一直走。"""
    if not state["alive"]:
        return {"action": "none", "reason": "已经死了"}
    if state["energy"] <= 1 and world.get("food"):
        return {"action": "eat", "reason": "赌徒：再不成就没命赌了"}
    if world.get("food") and roll < 0.15:
        return {"action": "eat", "reason": "赌徒：手气到了，吃一口"}
    return {"action": "move", "reason": "赌徒：下一格可能更好"}


def main() -> int:
    state = initial_state(0)
    print("一只赌徒水母的一生：")
    for _ in range(60):
        world = default_world(state["tick"], 0)
        roll = ((state["tick"] * 2654435761) % 1000) / 1000.0
        state, record = step(state, world, roll, gambler)
        if not state["alive"]:
            print("  第 %d 天饿死（走了 %d 次，只吃了 %d 次）" % (state["tick"], state["moved"], state["eaten"]))
            return 0
    print("  活了 60 天还没死（少见）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
