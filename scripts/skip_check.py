# INSTAR skip+main check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/skip_check.py
#
# Every public HTML page needs a skip link to #main and a main#main
# landmark. Cooks who copy a chamber can drop either. This script
# does not fetch and does not name a molt answer.
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
SKIP = re.compile(r'<a\s+class="skip"\s+href="#main">', re.I)
MAIN = re.compile(r"<main\b[^>]*\bid=['\"]main['\"]", re.I)


def html_rel(path: Path) -> str:
    return path.relative_to(PUB).as_posix()


def scan_public() -> list[str]:
    fails: list[str] = []
    pages = sorted(PUB.rglob("*.html"))
    if not pages:
        fails.append("no public HTML pages")
        return fails
    for path in pages:
        if "fonts" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        rel = html_rel(path)
        if not SKIP.search(text):
            fails.append(rel + " missing skip to #main")
        if not MAIN.search(text):
            fails.append(rel + " missing main#main")
    return fails


def main() -> int:
    fails = scan_public()
    if fails:
        print("SKIP CHECK FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("SKIP OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
