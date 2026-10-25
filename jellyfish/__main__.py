"""命令行：serve / tick / state / export"""
from __future__ import annotations

import json
import sys

from .log import Life
from .textio import force_utf8
from .server import serve


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
    if cmd in ("--version", "version"):
        from . import __version__

        print("jellyfish " + __version__)
        return 0

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
    if cmd == "fork":
        seed = int(argv[argv.index("--from-seed") + 1]) if "--from-seed" in argv else 0
        ticks = int(argv[argv.index("--ticks") + 1]) if "--ticks" in argv else 0
        dest_root = argv[argv.index("--to") + 1] if "--to" in argv else "my-life"
        source = Life(root, name=name, policy=policy)
        adopted = source.adopt(dest_root, seed=seed, ticks=ticks, name=name, policy=policy)
        print("已领养：" + dest_root + "（种子 %d，第 %d 天）" % (seed, adopted.state()["tick"]))
        print(adopted.biography())
        print()
        print("继续养：python -m jellyfish tick --root " + dest_root + " --name " + name + " --times 10")
        return 0
    if cmd == "movie":
        from .movie import write as write_movie

        out = argv[argv.index("--out") + 1] if "--out" in argv else "life-movie.svg"
        print("已生成 " + write_movie(Life(root, name=name, policy=policy), out))
        return 0
    if cmd == "card":
        from .card import write as write_card

        out = argv[argv.index("--out") + 1] if "--out" in argv else "card.svg"
        print("已生成 " + write_card(Life(root, name=name, policy=policy), out))
        return 0
    if cmd == "export":
        from .export import write_page
        out = argv[argv.index("--out") + 1] if "--out" in argv else "life.html"
        print("已导出 " + write_page(Life(root), out))
        return 0
    print("用法：python -m jellyfish [serve|tick|state|export|card|movie|fork] [--root .life] [--port 8080] [--name 名字] [--policy 性格]")
    return 2


if __name__ == "__main__":
    force_utf8()
    sys.exit(main())