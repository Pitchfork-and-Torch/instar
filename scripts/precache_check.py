# INSTAR PWA precache check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/precache_check.py
#
# After a new chamber, cooks must list it in public/sw.js and bump
# CACHE so pilgrims shed the old shell. This script does not fetch
# and does not name a molt answer. It fails when the offline school
# drifted:
#   - KILL is true (the school would unregister itself)
#   - a PRECACHE path is missing on disk
#   - a public chamber is missing from PRECACHE
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
SW = PUB / "sw.js"

KILL_RE = re.compile(r"const KILL\s*=\s*(true|false)\s*;")
CACHE_RE = re.compile(r'const CACHE\s*=\s*"([^"]+)"\s*;')
LIST_RE = re.compile(r"const PRECACHE\s*=\s*\[(.*?)\]\s*;", re.S)
ITEM_RE = re.compile(r'"(/[^"]*)"')
CACHE_NAME = re.compile(r"^instar-[0-9]+(?:\.[0-9]+)*$")
SKIP_DIRS = {"fonts"}


def parse_sw(text: str) -> tuple[bool | None, str, list[str]]:
    km = KILL_RE.search(text)
    cm = CACHE_RE.search(text)
    lm = LIST_RE.search(text)
    kill = None if not km else km.group(1) == "true"
    cache = cm.group(1) if cm else ""
    items = ITEM_RE.findall(lm.group(1)) if lm else []
    return kill, cache, items


def public_file(url: str) -> Path:
    if url == "/":
        return PUB / "index.html"
    rel = url.lstrip("/")
    if url.endswith("/"):
        return PUB / rel / "index.html"
    return PUB / rel


def chamber_urls() -> list[str]:
    out = ["/"]
    for path in sorted(PUB.glob("*/index.html")):
        if path.parent.name in SKIP_DIRS:
            continue
        out.append("/" + path.parent.name + "/")
    return out


def scan_sw(text: str) -> list[str]:
    fails: list[str] = []
    kill, cache, items = parse_sw(text)
    if kill is None:
        fails.append("public/sw.js has no KILL switch")
    elif kill:
        fails.append("public/sw.js KILL is true (would unregister the school)")
    if not CACHE_NAME.match(cache):
        fails.append("public/sw.js CACHE name is not instar-<version>")
    if not items:
        fails.append("public/sw.js PRECACHE is empty")

    seen: set[str] = set()
    for url in items:
        if url in seen:
            fails.append("PRECACHE lists " + url + " twice")
        seen.add(url)
        path = public_file(url)
        if not path.is_file():
            fails.append("PRECACHE path missing on disk: " + url)

    for url in chamber_urls():
        if url not in seen:
            fails.append("chamber not in PRECACHE: " + url)

    for url in ("/js/page56.js", "/js/puzzle.js", "/js/core.js"):
        if url not in seen:
            fails.append("school script not in PRECACHE: " + url)
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    sample = (
        "const KILL = false;\n"
        'const CACHE = "instar-1.0.0";\n'
        "const PRECACHE = [\n"
        '  "/",\n'
        '  "/husk/",\n'
        '  "/js/page56.js",\n'
        "];\n"
    )
    kill, cache, items = parse_sw(sample)
    if kill or cache != "instar-1.0.0" or items != ["/", "/husk/", "/js/page56.js"]:
        fails.append("sw parser miss")
    if not scan_sw(sample.replace("false", "true", 1)):
        fails.append("KILL true not flagged")
    if not scan_sw(sample.replace("/husk/", "/missing/", 1)):
        fails.append("missing PRECACHE path not flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("PRECACHE SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    if not SW.is_file():
        print("PRECACHE FAIL", file=sys.stderr)
        print("  public/sw.js is missing", file=sys.stderr)
        return 1
    fails = scan_sw(SW.read_text(encoding="utf-8"))
    if fails:
        print("PRECACHE FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("PRECACHE OK")
    print("offline school lists every chamber, and every listed path exists.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
