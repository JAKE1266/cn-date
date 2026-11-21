"""命令行入口：

    python -m cn_date "明天下午3点"
    python -m cn_date --now 2026-03-05T10:00 "下周一上午9点"
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime

from . import __version__
from .core import parse


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cn-date", description="中文自然语言日期解析")
    ap.add_argument("--version", action="version", version=f"cn-date {__version__}")
    ap.add_argument("text", nargs="+", help="一句中文（可多条，逐条解析）")
    ap.add_argument("--now", help="以指定时刻为基准（ISO 格式，缺省取当前时间）")
    args = ap.parse_args(argv)
    now = None
    if args.now:
        try:
            now = datetime.fromisoformat(args.now)
        except ValueError:
            print(f"错误：--now 需为 ISO 时间，如 2026-03-05T10:00", file=sys.stderr)
            return 2
    rc = 0
    for text in args.text:
        r = parse(text, now)
        if r is None:
            print(f"{text}  → 无法解析")
            rc = 1
        else:
            flags = "".join([("D" if r.has_date else ""), ("T" if r.has_time else "")]) or "-"
            print(f"{text}  →  {r.dt:%Y-%m-%d %H:%M}  [{flags}]")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
