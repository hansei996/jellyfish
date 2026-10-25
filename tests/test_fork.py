"""一键领养：同种子 + 同天数必须得到同一只。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jellyfish.log import Life  # noqa: E402


def test_adopt_reproduces_the_same_life(tmp_path):
    direct = Life(tmp_path / "a", seed=42, name="原版")
    for _ in range(12):
        if direct.state()["alive"]:
            direct.tick()

    source = Life(tmp_path / "src", seed=42, name="原版")
    adopted = source.adopt(tmp_path / "b", seed=42, ticks=12, name="我的水母")

    assert adopted.state()["tick"] == direct.state()["tick"]
    assert adopted.state()["eaten"] == direct.state()["eaten"]
    assert adopted.biography() != direct.biography(), "名字不同，传记就该不同"


def test_adopt_stops_at_death_and_says_so(tmp_path):
    source = Life(tmp_path / "s2", seed=3, name="x")
    adopted = source.adopt(tmp_path / "b2", seed=3, ticks=200, name="x")
    state = adopted.state()
    if not state["alive"]:
        assert state["death_reason"], "死了就必须有死因"


def test_fork_cli_works(tmp_path):
    proc = subprocess.run(
        [sys.executable, "jellyfish.py", "fork", "--from-seed", "42", "--ticks", "10",
         "--name", "我的水母", "--to", str(tmp_path / "mine")],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "已领养" in proc.stdout
    log = tmp_path / "mine" / "life.jsonl"
    assert log.exists() and log.read_text(encoding="utf-8").strip()
    json.loads(log.read_text(encoding="utf-8").splitlines()[0])
