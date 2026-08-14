# INSTAR search-listing check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/listing_check.py
#
# Hello, workbench, and the field manual are the public doors.
# Molt chambers stay noindex so a cook does not list the puzzle
# path in search. This script does not fetch and does not name a
# molt answer. It fails when the listing house drifted:
#   - a public door has noindex
#   - a chamber is missing noindex
#   - sitemap.xml lists a chamber, or drops a public door
#   - robots.txt loses the sitemap or the public Allows
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
HOST = "https://instar.jonbailey.xyz"
DOORS = ("/", "/workbench/", "/manual/")
SKIP_DIRS = {"fonts"}
NOINDEX = re.compile(r'<meta\s+name="robots"\s+content="[^"]*\bnoindex\b[^"]*"', re.I)
LOC = re.compile(r"<loc>\s*([^<]+)\s*</loc>", re.I)
SITEMAP_LINE = re.compile(r"(?im)^Sitemap:\s*(\S+)\s*$")
ALLOW_LINE = re.compile(r"(?im)^Allow:\s*(\S+)\s*$")
DISALLOW_ALL = re.compile(r"(?im)^Disallow:\s*/\s*$")


def url_of(rel_dir: str) -> str:
    if rel_dir == ".":
        return "/"
    return "/" + rel_dir.strip("/") + "/"


def chamber_urls() -> list[str]:
    out: list[str] = []
    for path in sorted(PUB.glob("*/index.html")):
        name = path.parent.name
        if name in SKIP_DIRS:
            continue
        url = url_of(name)
        if url not in DOORS:
            out.append(url)
    return out


def html_noindex(text: str) -> bool:
    return bool(NOINDEX.search(text))


def sitemap_locs(text: str) -> list[str]:
    locs: list[str] = []
    for m in LOC.finditer(text):
        raw = m.group(1).strip()
        if raw.startswith(HOST):
            path = raw[len(HOST) :] or "/"
            if not path.endswith("/") and path != "/":
                path = path + "/"
            if path == "":
                path = "/"
            locs.append(path)
        else:
            locs.append(raw)
    return locs


def scan_listing() -> list[str]:
    fails: list[str] = []
    for url, rel in (
        ("/", "index.html"),
        ("/workbench/", "workbench/index.html"),
        ("/manual/", "manual/index.html"),
    ):
        path = PUB / rel
        if not path.is_file():
            fails.append("public door missing: " + url)
            continue
        if html_noindex(path.read_text(encoding="utf-8")):
            fails.append(url + " is noindex (public door)")

    for url in chamber_urls():
        path = PUB / url.strip("/") / "index.html"
        if not path.is_file():
            fails.append("chamber missing: " + url)
            continue
        if not html_noindex(path.read_text(encoding="utf-8")):
            fails.append(url + " missing noindex")

    sm = PUB / "sitemap.xml"
    if not sm.is_file():
        fails.append("public/sitemap.xml is missing")
    else:
        locs = sitemap_locs(sm.read_text(encoding="utf-8"))
        for url in DOORS:
            if url not in locs:
                fails.append("sitemap.xml missing public door " + url)
        extra = [u for u in locs if u not in DOORS]
        if extra:
            fails.append("sitemap.xml lists a non-door path")

    rb = PUB / "robots.txt"
    if not rb.is_file():
        fails.append("public/robots.txt is missing")
        return fails
    robots = rb.read_text(encoding="utf-8")
    if DISALLOW_ALL.search(robots):
        fails.append("robots.txt Disallow: / hides the school")
    sm_line = SITEMAP_LINE.search(robots)
    if not sm_line or sm_line.group(1) != HOST + "/sitemap.xml":
        fails.append("robots.txt missing Sitemap: " + HOST + "/sitemap.xml")
    allows = {m.group(1) for m in ALLOW_LINE.finditer(robots)}
    for url in DOORS:
        if url not in allows:
            fails.append("robots.txt missing Allow: " + url)
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    if not html_noindex('<meta name="robots" content="noindex">'):
        fails.append("noindex detector miss")
    if html_noindex('<link rel="canonical" href="https://example/">'):
        fails.append("canonical flagged as noindex")
    locs = sitemap_locs(
        "<urlset><url><loc>" + HOST + "/</loc></url>"
        "<url><loc>" + HOST + "/workbench/</loc></url></urlset>"
    )
    if locs != ["/", "/workbench/"]:
        fails.append("sitemap loc parser miss")
    if "/husk/" not in chamber_urls():
        fails.append("chamber list missed /husk/")
    if "/workbench/" in chamber_urls():
        fails.append("workbench treated as a chamber")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("LISTING SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    fails = scan_listing()
    if fails:
        print("LISTING FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("LISTING OK")
    print("public doors stay listed; molt chambers stay noindex.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
