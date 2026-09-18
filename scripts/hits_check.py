# INSTAR hits-slug check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/hits_check.py
#
# Public doors carry the hits snippet. Cooks who copy a door can
# drop data-site="instar" or lose the script. This script does not
# fetch and does not name a molt answer. It fails when the slug
# house drifted:
#   - a public door is missing the hits snippet
#   - a public HTML page has the script without slug instar
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
DOORS = (
    ("/", "index.html"),
    ("/workbench/", "workbench/index.html"),
    ("/manual/", "manual/index.html"),
)
HITS_HOST = "hits.jonbailey.xyz/c.js"
SLUG = re.compile(
    r'hits\.jonbailey\.xyz/c\.js[^>]*data-site="instar"', re.I
)


def html_rel(path: Path) -> str:
    return path.relative_to(PUB).as_posix()


def scan_html(rel: str, text: str, require: bool) -> list[str]:
    fails: list[str] = []
    has_script = HITS_HOST in text
    has_slug = bool(SLUG.search(text))
    if require and not has_slug:
        fails.append(rel + " missing hits slug instar")
    elif has_script and not has_slug:
        fails.append(rel + " hits snippet missing slug instar")
    return fails


def scan_public() -> list[str]:
    fails: list[str] = []
    door_rels = {rel for _url, rel in DOORS}
    pages = sorted(PUB.rglob("*.html"))
    if not pages:
        fails.append("no public HTML pages")
        return fails
    for path in pages:
        rel = html_rel(path)
        fails += scan_html(
            rel,
            path.read_text(encoding="utf-8"),
            require=rel in door_rels,
        )
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    good = '<script defer src="https://hits.jonbailey.xyz/c.js" data-site="instar"></script>\n'
    if scan_html("index.html", good, True):
        fails.append("honest door flagged")
    if not scan_html("index.html", "<html lang=\"en\">\n", True):
        fails.append("missing door snippet not flagged")
    bare = '<script src="https://hits.jonbailey.xyz/c.js"></script>\n'
    if not scan_html("husk/index.html", bare, False):
        fails.append("script without slug not flagged")
    if scan_html("nymph/index.html", "<html lang=\"en\">\n", False):
        fails.append("chamber without hits flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("HITS SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    if not PUB.is_dir():
        print("HITS FAIL", file=sys.stderr)
        print("  public/ is missing", file=sys.stderr)
        return 1
    fails = scan_public()
    if fails:
        print("HITS FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("HITS OK")
    print("public doors still carry hits slug instar.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
