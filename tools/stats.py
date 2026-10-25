#!/usr/bin/env python3
"""stats —— 把这个仓库的硬指标算出来，README 里的数字必须和它一致。

硬指标（工程师决定要不要点进来时真正会看的）：
  测试数 / 包行数 / 单文件行数与字节 / 第三方依赖数（必须是 0）/ 支持平台

    python tools/stats.py            # 人读
    python tools/stats.py --json     # 给测试用
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STDLIB_HINT = {"__future__", "json", "sys", "os", "re", "hashlib", "math", "time", "random",
               "pathlib", "subprocess", "tempfile", "argparse", "http", "urllib", "xml",
               "datetime", "statistics", "shutil", "textwrap", "typing", "collections"}


def _force_utf8():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def count_tests():
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    for line in reversed(proc.stdout.strip().splitlines()):
        if "test" in line and "collected" in line:
            digits = "".join(ch for ch in line.split("test")[0] if ch.isdigit())
            if digits:
                return int(digits)
    return None


def loc(paths):
    total = 0
    for path in paths:
        total += len(path.read_text(encoding="utf-8").splitlines())
    return total


def third_party():
    """扫描包内 import，返回所有不属于标准库的名字。"""
    found = set()
    for path in (ROOT / "jellyfish").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
    external = {name for name in found if name not in STDLIB_HINT and not name.startswith("jellyfish")}
    return sorted(external)


def collect():
    single = ROOT / "jellyfish.py"
    package_files = sorted((ROOT / "jellyfish").glob("*.py")) + sorted((ROOT / "tools").glob("*.py"))
    return {
        "tests": count_tests(),
        "package_lines": loc(sorted((ROOT / "jellyfish").glob("*.py"))),
        "single_lines": len(single.read_text(encoding="utf-8").splitlines()),
        "single_bytes": single.stat().st_size,
        "dependencies": third_party(),
        "platforms": "ubuntu-latest + windows-latest",
        "python": "3.10 / 3.12",
    }


def main(argv):
    data = collect()
    if "--json" in argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    print("%-16s %s" % ("测试", data["tests"]))
    print("%-16s %d 行（jellyfish/）" % ("包", data["package_lines"]))
    print("%-16s %d 行 / %d 字节" % ("单文件", data["single_lines"], data["single_bytes"]))
    print("%-16s %d" % ("第三方依赖", len(data["dependencies"])))
    print("%-16s %s" % ("CI 平台", data["platforms"]))
    if data["dependencies"]:
        print()
        print("警告：出现第三方依赖 " + ", ".join(data["dependencies"]) + " —— 这个项目承诺零依赖")
        return 1
    return 0


if __name__ == "__main__":
    _force_utf8()
    sys.exit(main(sys.argv[1:]))
