"""README 里的硬指标必须与 tools/stats.py 算出来的一致 —— 手抄的数字迟早撒谎。"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _stats():
    proc = subprocess.run(
        [sys.executable, "tools/stats.py", "--json"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_readme_test_count_matches_reality():
    data = _stats()
    assert str(data["tests"]) in README, "README 里的测试数与实际不符（实际 %s）" % data["tests"]


def test_readme_single_file_size_matches_reality():
    data = _stats()
    kb = data["single_bytes"] / 1024
    assert "%.1f KB" % kb in README, "README 里的单文件大小与实际不符（实际 %.1f KB）" % kb


def test_readme_claims_zero_dependencies_and_it_is_true():
    data = _stats()
    assert data["dependencies"] == [], "出现了第三方依赖：" + str(data["dependencies"])
    assert "第三方依赖 | **0**" in README


def test_readme_states_the_supported_platforms():
    assert "ubuntu" in README and "windows" in README
