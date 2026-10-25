"""把标准输出钉成 UTF-8。

为什么单独一个模块：Windows 控制台默认 cp936，任何打印中文的入口（CLI、示例）都必须先钉死，
否则父进程按 utf-8 读就是乱码，甚至直接 UnicodeEncodeError 崩掉。
这个坑在本项目里已经踩过三次，所以做成一个可被所有入口复用的函数。
"""
from __future__ import annotations

import sys


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
