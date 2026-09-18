# INSTAR Pages headers check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/headers_check.py
#
# Cooks who touch public/_headers can drop nosniff, open CORS, or
# let sw.js cache forever. This script does not deploy and does not
# name a molt answer. It fails when the header house drifted:
#   - /* missing nosniff, referrer policy, or CSP default-src
#   - Access-Control-Allow-Origin is *
#   - /sw.js is not must-revalidate
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADERS = ROOT / "public" / "_headers"

PATH_RE = re.compile(r"^(/[^\s]*)$")
HDR_RE = re.compile(r"^  ([A-Za-z0-9!#$%&'*+.^_`|~-]+):\s*(.+)$")


def parse_headers(text: str) -> dict[str, dict[str, str]]:
    blocks: dict[str, dict[str, str]] = {}
    current = ""
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if not line or line.startswith("#"):
            continue
        pm = PATH_RE.match(line)
        if pm:
            current = pm.group(1)
            blocks.setdefault(current, {})
            continue
        hm = HDR_RE.match(line)
        if hm and current:
            blocks[current][hm.group(1)] = hm.group(2).strip()
    return blocks


def scan_headers(text: str) -> list[str]:
    fails: list[str] = []
    blocks = parse_headers(text)
    star = blocks.get("/*") or {}
    if not star:
        fails.append("public/_headers has no /* block")
        return fails

    if star.get("X-Content-Type-Options", "").lower() != "nosniff":
        fails.append("/* missing X-Content-Type-Options: nosniff")
    ref = star.get("Referrer-Policy", "").lower()
    if not ref or ref == "unsafe-url":
        fails.append("/* missing a safe Referrer-Policy")
    csp = star.get("Content-Security-Policy", "")
    if "default-src" not in csp:
        fails.append("/* CSP missing default-src")
    if "unsafe-eval" in csp:
        fails.append("/* CSP allows unsafe-eval")

    for path, hdrs in blocks.items():
        acao = hdrs.get("Access-Control-Allow-Origin", "")
        if acao == "*":
            fails.append(path + " opens CORS (*)")

    sw = blocks.get("/sw.js") or {}
    cache = sw.get("Cache-Control", "").lower()
    if "must-revalidate" not in cache and "max-age=0" not in cache:
        fails.append("/sw.js is not must-revalidate")
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    good = (
        "/*\n"
        "  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  Content-Security-Policy: default-src 'self'\n"
        "\n"
        "/sw.js\n"
        "  Cache-Control: public, max-age=0, must-revalidate\n"
    )
    if scan_headers(good):
        fails.append("honest headers flagged")
    if not scan_headers(good.replace("nosniff", "none")):
        fails.append("missing nosniff not flagged")
    open_cors = good + "\n/api\n  Access-Control-Allow-Origin: " + "*" + "\n"
    if not any("CORS" in x for x in scan_headers(open_cors)):
        fails.append("open CORS not flagged")
    sticky = good.replace("public, max-age=0, must-revalidate", "public, max-age=31536000, immutable")
    if not scan_headers(sticky):
        fails.append("sticky sw.js cache not flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("HEADERS SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    if not HEADERS.is_file():
        print("HEADERS FAIL", file=sys.stderr)
        print("  public/_headers is missing", file=sys.stderr)
        return 1
    fails = scan_headers(HEADERS.read_text(encoding="utf-8"))
    if fails:
        print("HEADERS FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("HEADERS OK")
    print("Pages _headers still has nosniff, a safe referrer policy, CSP,")
    print("no open CORS, and a must-revalidate service worker.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
