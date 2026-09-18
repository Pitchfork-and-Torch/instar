# INSTAR cache-freshness check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/fresh_check.py
#
# Cooks who edit public/_headers can make llms.txt or sitemap.xml
# sticky, or serve the webmanifest without a type under nosniff.
# This script does not deploy and does not name a molt answer. It
# fails when the living files drifted:
#   - /llms.txt, /sitemap.xml, or /sw.js is not must-revalidate
#   - /manifest.webmanifest is immutable or year-long
#   - /manifest.webmanifest missing Content-Type application/manifest+json
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import headers_check as hdr  # noqa: E402

HEADERS = ROOT / "public" / "_headers"
FRESH = ("/llms.txt", "/sitemap.xml", "/sw.js")
MANIFEST = "/manifest.webmanifest"
MANIFEST_TYPE = "application/manifest+json"


def is_fresh(cache: str) -> bool:
    low = cache.lower()
    return "must-revalidate" in low or "max-age=0" in low


def is_sticky(cache: str) -> bool:
    low = cache.lower()
    return "immutable" in low or "max-age=31536000" in low


def scan_fresh(text: str) -> list[str]:
    fails: list[str] = []
    blocks = hdr.parse_headers(text)
    for path in FRESH:
        cache = (blocks.get(path) or {}).get("Cache-Control", "")
        if not is_fresh(cache):
            fails.append(path + " is not must-revalidate")
    man = blocks.get(MANIFEST) or {}
    if not man:
        fails.append(MANIFEST + " block is missing")
        return fails
    ctype = man.get("Content-Type", "").lower()
    if MANIFEST_TYPE not in ctype:
        fails.append(MANIFEST + " missing Content-Type " + MANIFEST_TYPE)
    cache = man.get("Cache-Control", "")
    if is_sticky(cache):
        fails.append(MANIFEST + " is sticky")
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    good = (
        "/llms.txt\n"
        "  Cache-Control: public, max-age=0, must-revalidate\n"
        "/sitemap.xml\n"
        "  Cache-Control: public, max-age=0, must-revalidate\n"
        "/sw.js\n"
        "  Cache-Control: public, max-age=0, must-revalidate\n"
        "/manifest.webmanifest\n"
        "  Content-Type: application/manifest+json\n"
        "  Cache-Control: public, max-age=3600\n"
    )
    if scan_fresh(good):
        fails.append("honest headers flagged")
    sticky_llms = good.replace(
        "/llms.txt\n  Cache-Control: public, max-age=0, must-revalidate\n",
        "/llms.txt\n  Cache-Control: public, max-age=31536000, immutable\n",
    )
    if not scan_fresh(sticky_llms):
        fails.append("sticky llms.txt not flagged")
    no_type = good.replace("  Content-Type: application/manifest+json\n", "")
    if not any("Content-Type" in x for x in scan_fresh(no_type)):
        fails.append("missing manifest type not flagged")
    sticky_man = good.replace("max-age=3600", "max-age=31536000, immutable")
    if not any("sticky" in x for x in scan_fresh(sticky_man)):
        fails.append("sticky manifest not flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("FRESH SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    if not HEADERS.is_file():
        print("FRESH FAIL", file=sys.stderr)
        print("  public/_headers is missing", file=sys.stderr)
        return 1
    fails = scan_fresh(HEADERS.read_text(encoding="utf-8"))
    if fails:
        print("FRESH FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("FRESH OK")
    print("llms, sitemap, and sw.js stay must-revalidate. Manifest keeps its type.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
