# INSTAR canonical-host check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/canon_check.py
#
# Public doors (hello, workbench, manual) carry a canonical URL.
# Cooks who copy a door can leave the wrong href, point off-host,
# or publish an onion. This script does not fetch and does not
# name a molt answer. It fails when the host house drifted:
#   - a public door is missing its on-host canonical
#   - a canonical or alternate href is off-host or an onion
#   - a canonical href does not match the page path
#   - 404.html claims a canonical (the miss page is not a door)
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import cook_guard as guard  # noqa: E402

PUB = ROOT / "public"
HOST = "https://instar.jonbailey.xyz"
DOORS = (
    ("/", "index.html"),
    ("/workbench/", "workbench/index.html"),
    ("/manual/", "manual/index.html"),
)
LINK = re.compile(r"<link\b[^>]*>", re.I)
REL = re.compile(r'\brel="([^"]+)"', re.I)
HREF = re.compile(r'\bhref="([^"]+)"', re.I)
ABS_URL = re.compile(r"^https?://", re.I)


def html_rel(path: Path) -> str:
    return path.relative_to(PUB).as_posix()


def url_of(rel: str) -> str:
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("/index.html")] + "/"
    return "/" + rel


def link_hrefs(text: str, rel_name: str) -> list[str]:
    out: list[str] = []
    want = rel_name.lower()
    for tag in LINK.finditer(text):
        raw = tag.group(0)
        rm = REL.search(raw)
        hm = HREF.search(raw)
        if not rm or not hm:
            continue
        rels = {part.strip().lower() for part in rm.group(1).split()}
        if want in rels:
            out.append(hm.group(1).strip())
    return out


def href_kind(href: str) -> str:
    extra = guard.unknown_onions(href, guard.teaching_onions())
    if extra or ".onion" in href.lower():
        return "onion"
    if ABS_URL.match(href):
        if href.startswith(HOST + "/") or href == HOST or href == HOST + "/":
            return "host"
        return "off-host"
    if href.startswith("/"):
        return "root"
    return "relative"


def expected_canonical(url: str) -> str:
    if url == "/":
        return HOST + "/"
    return HOST + url


def scan_page(rel: str, text: str, is_door: bool, is_404: bool) -> list[str]:
    fails: list[str] = []
    canons = link_hrefs(text, "canonical")
    alts = link_hrefs(text, "alternate")
    if is_404:
        if canons:
            fails.append(rel + " has a canonical (miss page is not a door)")
        return fails
    if is_door:
        if not canons:
            fails.append(rel + " missing canonical")
        elif len(canons) > 1:
            fails.append(rel + " has more than one canonical")
        else:
            want = expected_canonical(url_of(rel))
            if canons[0] != want:
                fails.append(rel + " canonical is not " + want)
    for href in canons + alts:
        kind = href_kind(href)
        if kind == "onion":
            fails.append(rel + " link is an onion (do not publish onions)")
        elif kind == "off-host":
            fails.append(rel + " link is off-host")
        elif kind == "relative":
            fails.append(rel + " link is not a root-relative or on-host URL")
        elif kind == "root" and href in canons:
            fails.append(rel + " canonical must be the absolute host URL")
    if not is_door and canons:
        want = expected_canonical(url_of(rel))
        if canons[0] != want:
            fails.append(rel + " canonical does not match this page")
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
        fails += scan_page(
            rel,
            path.read_text(encoding="utf-8"),
            is_door=rel in door_rels,
            is_404=rel == "404.html",
        )
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    hello = '<link rel="canonical" href="' + HOST + '/">\n'
    if scan_page("index.html", hello, True, False):
        fails.append("honest hello flagged")
    work = '<link rel="canonical" href="' + HOST + '/workbench/">\n'
    if scan_page("workbench/index.html", work, True, False):
        fails.append("honest workbench flagged")
    if not scan_page("index.html", "<html lang=\"en\">\n", True, False):
        fails.append("missing door canonical not flagged")
    wrong = '<link rel="canonical" href="' + HOST + '/manual/">\n'
    if not scan_page("index.html", wrong, True, False):
        fails.append("wrong-path canonical not flagged")
    onion = '<link rel="canonical" href="http://' + ("a" * 16) + '.onion/">\n'
    if not any("onion" in x for x in scan_page("index.html", onion, True, False)):
        fails.append("onion canonical not flagged")
    off = '<link rel="canonical" href="https://example.com/">\n'
    if not any("off-host" in x for x in scan_page("index.html", off, True, False)):
        fails.append("off-host canonical not flagged")
    if not scan_page("404.html", hello, False, True):
        fails.append("404 canonical not flagged")
    if scan_page("404.html", "<html lang=\"en\">\n", False, True):
        fails.append("honest 404 flagged")
    if scan_page("husk/index.html", "<html lang=\"en\">\n", False, False):
        fails.append("chamber without canonical flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("CANON SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    if not PUB.is_dir():
        print("CANON FAIL", file=sys.stderr)
        print("  public/ is missing", file=sys.stderr)
        return 1
    fails = scan_public()
    if fails:
        print("CANON FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("CANON OK")
    print("public doors keep an on-host canonical. No onion. No off-host.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
