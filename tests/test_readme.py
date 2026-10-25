"""README 里的命令必须真能跑 —— 按读者顺序，一条接一条地跑。"""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")

# 这些命令会在原地阻塞、递归或覆盖生成物，单测里跑不了（各自有别的测试覆盖）
SKIP = ("serve", "pytest", "build_single.py", "preflight.py")  # preflight 自己会跑测试，读了它就会无限递归


def commands():
    out = []
    for block in README.split("```bash")[1:]:
        for line in block.split("```")[0].splitlines():
            line = line.strip()
            if not line.startswith("python "):
                continue
            line = line.split(" #")[0].strip()
            if any(skip in line for skip in SKIP):
                continue
            out.append(line)
    return out


def test_readme_has_runnable_commands():
    assert len(commands()) >= 4, "README 里应当有 4 条以上可直接跑的命令"


def test_reader_can_follow_the_readme_top_to_bottom(tmp_path):
    """按 README 的顺序、共用一个 demo 目录跑一遍 —— 读者就是这么做的。"""
    demo = tmp_path / "demo"
    for command in commands():
        rewritten = command.replace("--root demo", "--root " + shlex.quote(str(demo)))
        for name in ("life.html", "card.svg", "demo.svg", "life-movie.svg"):
            rewritten = rewritten.replace("--out " + name, "--out " + shlex.quote(str(tmp_path / name)))
        proc = subprocess.run(
            [sys.executable, *shlex.split(rewritten)[1:]],
            cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
        assert proc.returncode == 0, command + " 跑不通：" + chr(10) + proc.stdout + proc.stderr


def test_readme_mentions_the_real_entry_points():
    for needle in ("jellyfish.py", "python -m jellyfish", "card", "movie", "export", "docs/EXTEND.md"):
        assert needle in README, "README 里少了：" + needle