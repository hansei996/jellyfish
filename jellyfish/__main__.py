"""命令行：serve / tick / state / export"""
from __future__ import annotations

import json
import sys

from .log import Life
from .server import serve


def _force_utf8():
    """钉成 UTF-8：Windows 控制台默认 cp936，脚本输出被父进程按 utf-8 读就是乱码。

    这个坑在本项目的历史上已经踩过两次（校验器、查看器），所以 CLI 入口一律钉死。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = ".life"
    name = "小水母"
    if "--root" in argv:
        root = argv[argv.index("--root") + 1]
    if "--name" in argv:
        name = argv[argv.index("--name") + 1]
    policy = argv[argv.index("--policy") + 1] if "--policy" in argv else "balanced"
    cmd = argv[0] if argv else "serve"

    if cmd == "serve":
        port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8080
        serve(root, port=port)
        return 0
    if cmd == "tick":
        life = Life(root, name=name, policy=policy)
        n = int(argv[argv.index("--times") + 1]) if "--times" in argv else 1
        for _ in range(n):
            if life.state()["alive"]:
                life.tick()
        state = life.state()
        print(json.dumps(state, ensure_ascii=False))
        return 0
    if cmd == "state":
        print(json.dumps(Life(root).state(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "export":
        from .export import write_page
        out = argv[argv.index("--out") + 1] if "--out" in argv else "life.html"
        print("已导出 " + write_page(Life(root), out))
        return 0
    print("用法：python -m jellyfish [serve|tick|state|export] [--root .life] [--port 8080]")
    return 2


if __name__ == "__main__":
    _force_utf8()
    sys.exit(main())