"""可扩展性：自定义 policy（函数）必须能用，且仍可重放。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jellyfish.core import initial_state, step  # noqa: E402
from jellyfish.log import Life  # noqa: E402


def always_eat(state, world, roll):
    if not state["alive"]:
        return {"action": "none", "reason": "死了"}
    if world.get("food"):
        return {"action": "eat", "reason": "无脑吃"}
    return {"action": "move", "reason": "找吃的"}


def test_custom_policy_function_is_accepted():
    state = initial_state(0)
    state, record = step(state, {"food": 1}, 0.5, always_eat)
    assert record["decision"]["action"] == "eat"


def test_custom_policy_life_is_replayable(tmp_path):
    life = Life(tmp_path, seed=0, policy=always_eat)
    for _ in range(10):
        if life.state()["alive"]:
            life.tick()
    again = Life(tmp_path, seed=0, policy=always_eat)
    assert again.state() == life.state()


def test_every_example_runs():
    for name in ("01_custom_world.py", "02_custom_policy.py", "03_compare.py"):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "examples" / name)],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        assert proc.returncode == 0, name + " 跑不起来：\n" + proc.stdout + proc.stderr
        assert proc.stdout.strip(), name + " 没有任何输出"


def test_docs_mention_the_two_pure_function_rules():
    text = (ROOT / "docs" / "EXTEND.md").read_text(encoding="utf-8")
    assert "不读时间" in text
    assert "不改" in text
    assert "examples/03_compare.py" in text


def test_examples_emit_utf8_even_on_a_cp936_console():
    """Windows 控制台默认 cp936 —— 剥掉 PYTHONIOENCODING 后仍必须能按 utf-8 解码。"""
    import os

    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    for name in ("01_custom_world.py", "02_custom_policy.py", "03_compare.py"):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "examples" / name)],
            cwd=str(ROOT), capture_output=True, env=env,
        )
        assert proc.returncode == 0, name + " 在无编码变量时崩了：" + proc.stderr.decode("utf-8", "replace")
        text = proc.stdout.decode("utf-8")  # 解不出来就说明没有钉 UTF-8
        assert text.strip(), name + " 没有输出"


def test_cli_emits_utf8_without_the_env_var(tmp_path):
    import os

    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    env["PYTHONPATH"] = str(ROOT)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "jellyfish.py"), "tick", "--root", str(tmp_path / "u"), "--times", "3"],
        cwd=str(ROOT), capture_output=True, env=env,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    import json

    json.loads(proc.stdout.decode("utf-8").strip().splitlines()[-1])
