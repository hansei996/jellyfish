#!/usr/bin/env python3
"""traffic —— 每天读一次真实数据，写进 docs/LAUNCH-LOG.md。

只读公开数据（stars / forks / issues）和仓库自己的 traffic（需要 push 权限，我们有）。
不刷、不求、不互 star —— 这个脚本只负责如实记录。

    python tools/traffic.py            # 追加一行到今天
    python tools/traffic.py --print    # 只看，不写
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "docs" / "LAUNCH-LOG.md"
REPO = "hansei996/jellyfish"


def _force_utf8():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def gh(*args):
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def collect():
    code, out = gh("api", "repos/" + REPO)
    if code != 0:
        raise SystemExit("读仓库信息失败：" + out[:200])
    repo = json.loads(out)
    row = {
        "date": date.today().isoformat(),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "watchers": repo.get("subscribers_count", 0),
        "issues": repo.get("open_issues_count", 0),
        "views": None,
        "uniques": None,
    }
    code, out = gh("api", "repos/" + REPO + "/traffic/views")
    if code == 0 and out.strip():
        data = json.loads(out)
        row["views"] = data.get("count")
        row["uniques"] = data.get("uniques")
    return row


def render(row):
    cells = [
        row["date"], row["stars"], row["forks"], row["watchers"], row["issues"],
        "-" if row["views"] is None else row["views"],
        "-" if row["uniques"] is None else row["uniques"],
    ]
    return "| " + " | ".join(str(c) for c in cells) + " |"


HEAD = chr(10).join([
    "# 发布日志（每天一行，如实记录）",
    "",
    "> 由 tools/traffic.py 生成。不刷、不求 star、不互 star。",
    "",
    "| 日期 | stars | forks | watchers | open issues | 近 14 天 views | uniques |",
    "|---|---|---|---|---|---|---|",
    "",
])


def main(argv):
    row = collect()
    line = render(row)
    if "--print" in argv:
        print(line)
        return 0
    if not LOG.exists():
        LOG.write_text(HEAD + line + chr(10), encoding="utf-8")
    else:
        text = LOG.read_text(encoding="utf-8")
        if row["date"] in text:
            lines = [line if l.startswith("| " + row["date"]) else l for l in text.splitlines()]
            LOG.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
        else:
            LOG.write_text(text.rstrip(chr(10)) + chr(10) + line + chr(10), encoding="utf-8")
    print(line)
    print()
    if row["stars"] == 0 and (row["uniques"] or 0) == 0:
        print("判读：还没有人来过。瓶颈是渠道，不是产品 —— 现在改代码都是盲改。")
    elif (row["uniques"] or 0) > 50 and row["stars"] < 2:
        print("判读：有人来但没 star。瓶颈是首屏，该改第一张图和第一句话。")
    else:
        print("判读：见 docs/LAUNCH.md 的「发布后 48 小时看什么」。")
    return 0


if __name__ == "__main__":
    _force_utf8()
    sys.exit(main(sys.argv[1:]))
