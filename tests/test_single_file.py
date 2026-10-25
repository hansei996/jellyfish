"""单文件版必须与包版本行为完全一致，且必须是生成出来的。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SINGLE = ROOT / "jellyfish.py"


def _run_single(args, cwd):
    return subprocess.run(
        [sys.executable, str(SINGLE), *args],
        cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def test_single_file_exists_and_runs(tmp_path):
    assert SINGLE.exists(), "先跑 python tools/build_single.py"
    proc = _run_single(["tick", "--root", str(tmp_path / "r"), "--times", "5"], ROOT)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (tmp_path / "r" / "life.jsonl").exists()


def test_single_file_cannot_diverge_from_the_package(tmp_path):
    """同一 seed 下，单文件与包必须产生一模一样的一生。"""
    sys.path.insert(0, str(ROOT))
    from jellyfish.log import Life

    package_days = []
    life = Life(tmp_path / "pkg", seed=0)
    for _ in range(25):
        if life.state()["alive"]:
            life.tick()
    package_days = life.state()

    proc = _run_single(["tick", "--root", str(tmp_path / "sgl"), "--times", "25"], ROOT)
    assert proc.returncode == 0, proc.stderr
    import json

    single_state = json.loads(proc.stdout.strip().splitlines()[-1])
    assert single_state["tick"] == package_days["tick"]
    assert single_state["eaten"] == package_days["eaten"]
    assert single_state["moved"] == package_days["moved"]
    assert single_state["death_reason"] == package_days["death_reason"]


def test_single_file_is_regenerable_byte_for_byte(tmp_path):
    """CI 用这条防手改：生成物必须与仓库里的完全一致。"""
    out = tmp_path / "regen.py"
    proc = subprocess.run(
        [sys.executable, "tools/build_single.py", str(out)],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 0, proc.stderr
    assert out.read_text(encoding="utf-8") == SINGLE.read_text(encoding="utf-8"), \
        "jellyfish.py 被手改过，或者忘了重新生成"


def test_single_file_has_no_package_imports():
    text = SINGLE.read_text(encoding="utf-8")
    for banned in ("from jellyfish", "import jellyfish", "from .core", "from .log"):
        assert banned not in text, "单文件里不该出现：" + banned
