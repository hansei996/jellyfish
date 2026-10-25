"""生命的纯内核：状态只由 (旧状态, 世界, 这一次的随机值) 决定。

三条设计约束：
  1. 纯函数：step() 不读时钟、不读环境、不联网。随机性由**调用方**给出并写进日志，
     所以同一份日志永远重放出同一个生命。
  2. 可死：能量归零即死；触到红线即自毁。死亡不可撤销，只能由人复活（复活也是一条日志）。
  3. 可审计：每一步都记录观测、决策、理由和状态哈希。
"""
from __future__ import annotations

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
    return {"food": 1 if ((tick * 7 + seed * 13) % 5) in (0, 1) else 0}


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


def step(state: dict, world: dict, roll: float) -> tuple[dict, dict]:
    """返回 (新状态, 这一步的记录)。纯函数。"""
    decision = decide(state, world, roll)
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