#!/usr/bin/env python3
"""preflight —— 推送前必须全绿的四件事，做成脚本而不是纪律。

为什么要有它：我已经两次带着红测试推送了（都是"预期内的红"）。纪律靠不住，脚本靠得住。

    python tools/preflight.py        # 全过才允许 push

四步：
  1. 测试全绿（含 README 命令串跑）
  2. 单文件与包一致（重新生成后逐字节比较）
  3. 单文件能独立跑（tick + export + card + movie）
  4. 仓库里没有遗留的生成物（demo/、*.html、card.svg 等）
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _force_utf8():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def run(args, cwd=None, timeout=300):
    proc = subprocess.run(
        [sys.executable, *args], cwd=str(cwd or ROOT),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    results = []

    code, out = run(["-m", "pytest", "tests", "-q"])
    results.append(("测试全绿", code == 0, out.strip().splitlines()[-1] if out.strip() else ""))

    with tempfile.TemporaryDirectory() as tmp:
        regen = Path(tmp) / "regen.py"
        code, out = run(["tools/build_single.py", str(regen)])
        same = code == 0 and regen.exists() and regen.read_text(encoding="utf-8") == (ROOT / "jellyfish.py").read_text(encoding="utf-8")
        results.append(("单文件与包一致", same, "" if same else "重新生成后与仓库里的不一致"))

        demo = Path(tmp) / "demo"
        steps = [
            ["jellyfish.py", "tick", "--root", str(demo), "--times", "20"],
            ["jellyfish.py", "export", "--root", str(demo), "--out", str(Path(tmp) / "life.html")],
            ["jellyfish.py", "card", "--root", str(demo), "--out", str(Path(tmp) / "card.svg")],
            ["jellyfish.py", "movie", "--root", str(demo), "--out", str(Path(tmp) / "demo.svg")],
        ]
        failures = []
        for step in steps:
            code, out = run(step)
            if code != 0:
                failures.append(step[1] + ": " + out.strip().splitlines()[-1] if out.strip() else step[1])
        results.append(("单文件能独立跑完四个命令", not failures, "; ".join(failures)))

    junk = []
    for pattern in ("*.html", "card.svg", "demo.svg", "life.jsonl"):
        junk += [str(p.relative_to(ROOT)) for p in ROOT.glob(pattern)]
    for name in ("demo", "demo-life", "card-life", "movie-life", "single-test", "ui-life", "docs-example"):
        if (ROOT / name).exists():
            junk.append(name + "/")
    results.append(("没有遗留生成物", not junk, ", ".join(sorted(junk)[:5])))

    print("preflight")
    print("-" * 56)
    for name, ok, detail in results:
        print("%-6s %-26s %s" % ("PASS" if ok else "FAIL", name, detail if not ok else ""))
    failed = [name for name, ok, _ in results if not ok]
    print("-" * 56)
    if failed:
        print("结果：%d 项未通过 —— 不许推送" % len(failed))
        return 1
    print("结果：全过，可以推送")
    return 0


if __name__ == "__main__":
    _force_utf8()
    sys.exit(main())
