"""全仓守则：任何打印非 ASCII 的脚本，必须自己钉 UTF-8。

这个坑在本项目的历史上已经踩过三次（CLI、示例、构建脚本），
所以不再靠「记得」，改成一条会红的测试。
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCH = list((ROOT / "tools").glob("*.py")) + list((ROOT / "examples").glob("*.py")) + [ROOT / "jellyfish.py"]


def test_every_printing_script_pins_utf8():
    offenders = []
    for path in WATCH:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not any(ord(ch) > 127 for ch in text):
            continue
        if "print(" not in text:
            continue
        if "force_utf8" not in text and 'reconfigure(encoding="utf-8"' not in text:
            offenders.append(path.name)
    assert offenders == [], "这些脚本会按系统代码页输出，Windows 上会崩：" + ", ".join(offenders)


def test_build_script_survives_a_cp936_console(tmp_path):
    import os
    import subprocess
    import sys

    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    out = tmp_path / "regen.py"
    proc = subprocess.run(
        [sys.executable, "tools/build_single.py", str(out)],
        cwd=str(ROOT), capture_output=True, env=env,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert proc.stdout.decode("utf-8").strip(), "构建脚本没有任何可读输出"
