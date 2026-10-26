"""README 里的硬指标必须与 tools/stats.py 算出来的一致 —— 手抄的数字迟早撒谎。

注意一个坑：单文件的字节约等于行数 × 每行平均字节，**CRLF 与 LF 会差约 1 KB**。
所以行数精确比对，KB 给 ±2 的容差 —— 否则 Windows 本地绿、CI 上红（真的发生过）。
"""
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


def test_readme_single_file_lines_are_exact_and_size_is_close():
    data = _stats()
    match = re.search(r"单文件 \| \*\*(\d+) 行 / 约 (\d+) KB\*\*", README)
    assert match, "README 里没写「单文件 | **N 行 / 约 N KB**」"
    lines, kb = int(match.group(1)), int(match.group(2))
    assert lines == data["single_lines"], "行数不符：README %d，实际 %d" % (lines, data["single_lines"])
    actual_kb = data["single_bytes"] / 1024
    assert abs(kb - actual_kb) <= 2, "KB 差太多：README %d，实际 %.1f（CRLF/LF 最多差 1KB）" % (kb, actual_kb)


def test_readme_claims_zero_dependencies_and_it_is_true():
    data = _stats()
    assert data["dependencies"] == [], "出现了第三方依赖：" + str(data["dependencies"])
    assert "第三方依赖 | **0**" in README


def test_readme_states_the_supported_platforms():
    assert "ubuntu" in README and "windows" in README
