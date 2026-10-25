"""README 里的命令必须真能跑 —— 文档写了跑不通，比没写更糟。"""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")

# 这些命令会在原地阻塞、递归或覆盖生成物，单测里跑不了（各自有别的测试覆盖）
SKIP = ("serve", "pytest", "build_single.py")


def commands():
    out = []
    for block in README.split("```bash")[1:]:
        body = block.split("```")[0]
        for line in body.splitlines():
            line = line.strip()
            if not line.startswith("python "):
                continue
            line = line.split(" #")[0].strip()   # 行内注释是给人看的，不是命令的一部分
            if any(skip in line for skip in SKIP):
                continue
            out.append(line)
    return out


def test_readme_has_runnable_commands():
    found = commands()
    assert len(found) >= 3, "README 里应当至少有 3 条可直接跑的命令，实际：" + str(found)


@pytest.mark.parametrize("command", commands())
def test_readme_command_runs(command, tmp_path):
    rewritten = command.replace("--root demo", "--root " + shlex.quote(str(tmp_path / "r")))
    rewritten = rewritten.replace("--out life.html", "--out " + shlex.quote(str(tmp_path / "life.html")))
    rewritten = rewritten.replace("--out card.svg", "--out " + shlex.quote(str(tmp_path / "card.svg")))
    args = shlex.split(rewritten)[1:]
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    assert proc.returncode == 0, command + " 跑不通：" + chr(10) + proc.stdout + proc.stderr


def test_readme_mentions_the_real_entry_points():
    for needle in ("jellyfish.py", "python -m jellyfish", "card", "export", "docs/EXTEND.md"):
        assert needle in README, "README 里少了：" + needle