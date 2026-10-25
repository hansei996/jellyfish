"""人生日志：追加写 + 哈希链，任何一步都能重算。

日志是唯一的事实来源；内存里的状态只是缓存。
"""
from __future__ import annotations

import json
from pathlib import Path

from .core import canon, default_world, digest, initial_state, revive, step

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