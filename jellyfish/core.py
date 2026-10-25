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
START_ENERGY = 8
MAX_ENERGY = 10


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


def _mix(a: int, b: int) -> int:
    """把 (tick, seed) 混成一个伪随机数。

    上一版用 (tick*3 + seed*13) % 7：种子差 7 的整数倍时模 7 结果相同，
    于是 seed 0 / 7 / 42 得到了**完全相同的一生** —— 分享链接就没意义了。
    """
    x = ((a * 2654435761) ^ (b * 2246822519)) & 0xFFFFFFFF
    x ^= x >> 13
    x = (x * 1274126177) & 0xFFFFFFFF
    x ^= x >> 16
    return x


def default_world(tick: int, seed: int = 0) -> dict:
    """默认世界：食物稀缺、随天数变化，且**不同种子给不同的世界**。"""
    return {"food": 1 if _mix(tick + 1, seed) % 100 < 26 else 0}


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