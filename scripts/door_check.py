# INSTAR 404 / redirects check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/door_check.py
#
# Not every door is a door. Cooks who edit public/_redirects can point
# a miss at a live hidden service, or let the 404 page get indexed.
# This script does not fetch and does not name a molt answer. It fails
# when the miss-path drifted:
#   - public/_redirects or public/404.html is missing
#   - no 404 rule remains
#   - a redirect target is off-host or an onion
#   - 404.html is missing noindex
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
HOST = "https://instar.jonbailey.xyz"
RULE = re.compile(r"^(\S+)\s+(\S+)\s+(\d+)\s*$")
NOINDEX = re.compile(r'<meta\s+name="robots"\s+content="[^"]*\bnoindex\b[^"]*"', re.I)
ONION = re.compile(r"\.onion\b", re.I)
ABS_URL = re.compile(r"^https?://", re.I)


def parse_redirects(text: str) -> list[tuple[str, str, int]]:
    out: list[tuple[str, str, int]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = RULE.match(line)
        if not m:
            continue
        out.append((m.group(1), m.group(2), int(m.group(3))))
    return out


def target_ok(dest: str) -> str:
    if ONION.search(dest):
        return "onion"
    if ABS_URL.match(dest):
        if dest.startswith(HOST + "/") or dest == HOST or dest == HOST + "/":
            return ""
        return "off-host"
    if dest.startswith("/"):
        return ""
    return "relative"


def scan_doors(redirects: str, html404: str) -> list[str]:
    fails: list[str] = []
    rules = parse_redirects(redirects)
    if not rules:
        fails.append("public/_redirects has no rules")
        return fails
    if not any(status == 404 for _src, _dst, status in rules):
        fails.append("public/_redirects has no 404 rule")
    for _src, dest, status in rules:
        kind = target_ok(dest)
        if kind == "onion":
            fails.append("redirect target is an onion (do not publish onions)")
        elif kind == "off-host":
            fails.append("redirect target is off-host")
        elif kind == "relative":
            fails.append("redirect target is not a root-relative path")
        elif status == 404:
            rel = dest.lstrip("/")
            if not (PUB / rel).is_file():
                fails.append("404 target missing on disk: " + dest)
    if not NOINDEX.search(html404):
        fails.append("public/404.html missing noindex")
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    good_r = "/*    /404.html   404\n"
    good_h = '<meta name="robots" content="noindex">\n'
    if scan_doors(good_r, good_h):
        fails.append("honest 404/redirects flagged")
    if not scan_doors("", good_h):
        fails.append("empty redirects not flagged")
    onion = "/*    http://" + ("a" * 16) + ".onion/   302\n"
    if not any("onion" in x for x in scan_doors(onion, good_h)):
        fails.append("onion redirect not flagged")
    if not scan_doors(good_r, "<title>miss</title>\n"):
        fails.append("404 without noindex not flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("DOOR SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    red = PUB / "_redirects"
    html = PUB / "404.html"
    if not red.is_file():
        print("DOOR FAIL", file=sys.stderr)
        print("  public/_redirects is missing", file=sys.stderr)
        return 1
    if not html.is_file():
        print("DOOR FAIL", file=sys.stderr)
        print("  public/404.html is missing", file=sys.stderr)
        return 1
    fails = scan_doors(red.read_text(encoding="utf-8"), html.read_text(encoding="utf-8"))
    if fails:
        print("DOOR FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("DOOR OK")
    print("miss-path stays on-host, 404 stays noindex, no onion redirect.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
