#!/usr/bin/env python3
"""把包拼成一个单文件 jellyfish.py。

为什么用生成而不是手写两份：两份代码一定会分家。这里包是唯一事实来源，
单文件是构建产物；CI 会重新生成并断言与仓库里的那份完全一致。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _force_utf8():
    """这个脚本自己也打印中文，Windows 上同样会被 cp936 打崩。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
PKG = ROOT / "jellyfish"
ORDER = ("textio.py", "core.py", "log.py", "export.py", "card.py", "movie.py", "server.py")
HEADER = '''#!/usr/bin/env python3
"""jellyfish —— 养一只会死的水母。单文件版，零依赖。

    python jellyfish.py serve         # http://127.0.0.1:8080
    python jellyfish.py tick --times 30 --name 小水母
    python jellyfish.py state
    python jellyfish.py export --out life.html

这是从 jellyfish/ 包自动生成的（tools/build_single.py），不要直接改这个文件。
"""
'''
STRIP = re.compile(r"^\s*(from \.|from jellyfish|import jellyfish)[^\n]*\n", re.M)
# "from .card import write as write_card" 被删掉后，别名也得补回来
ALIAS = re.compile(r"^\s*from \.[a-z_]+ import (\w+) as (\w+)\s*$", re.M)


def strip_relative(text: str) -> str:
    aliases = ["%s = %s" % (new, old) for old, new in ALIAS.findall(text)]
    text = STRIP.sub("", text)
    if aliases:
        text = "\n".join(aliases) + "\n" + text
    text = re.sub(r"^from __future__ import annotations\n", "", text, flags=re.M)
    return text


def build() -> str:
    parts = [HEADER]
    for name in ORDER:
        body = strip_relative((PKG / name).read_text(encoding="utf-8"))
        body = re.sub(r'^""".*?"""\n', "", body, flags=re.S)  # 去掉模块 docstring
        parts.append("# " + "-" * 70 + "\n# 来自 jellyfish/" + name + "\n# " + "-" * 70 + "\n")
        parts.append(body.strip() + "\n\n")
    main_body = strip_relative((PKG / "__main__.py").read_text(encoding="utf-8"))
    main_body = re.sub(r'^""".*?"""\n', "", main_body, flags=re.S)
    main_body = main_body.replace("from .log import Life\n", "").replace("from .server import serve\n", "")
    parts.append("# " + "-" * 70 + "\n# 命令行\n# " + "-" * 70 + "\n")
    parts.append(main_body.strip() + "\n\n")
    parts.append('if __name__ == "__main__":\n    sys.exit(main())\n')
    return "\n".join(parts)


def main(argv):
    target = Path(argv[0]) if argv else ROOT / "jellyfish.py"
    text = build()
    target.write_text(text, encoding="utf-8")
    print("已生成 %s（%d 行）" % (target, text.count(chr(10))))
    return 0


if __name__ == "__main__":
    _force_utf8()
    sys.exit(main(sys.argv[1:]))