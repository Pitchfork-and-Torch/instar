# INSTAR Ensure-TweetCard. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/ensure_tweet_card.py
#
# After a visual or copy change, cooks bump og.jpg?v= and keep the
# hello tweet card honest. This script does not bump and does not
# deploy. It only fails when the card drifted:
#   - public/og.jpg missing or not a JPEG
#   - twitter:card is not summary_large_image
#   - og:image / twitter:image / JSON-LD image disagree on ?v=
#   - llms.txt version drifted from the card
#   - hello hits snippet loses slug instar
#   - workbench / manual share cards disagree on og.jpg?v=
#   - puzzle.js / sw.js / README version drifted from the card
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
HOST = "https://instar.jonbailey.xyz"
OG_NAME = "og.jpg"
CARD = "summary_large_image"

META = re.compile(
    r'<meta\s+(?:property|name)="([^"]+)"\s+content="([^"]*)"',
    re.I,
)
VER = re.compile(r"^(?:[\-\*]\s*)?Version:\s*(\S+)\s*$", re.M)
OG_URL = re.compile(r"^https://instar\.jonbailey\.xyz/og\.jpg\?v=([0-9]+(?:\.[0-9]+)*)$")
HITS = re.compile(r'hits\.jonbailey\.xyz/c\.js[^>]*data-site="instar"')
PUZZLE_V = re.compile(r'"v"\s*:\s*"([^"]+)"')
SW_CACHE = re.compile(r'CACHE\s*=\s*"instar-([^"]+)"')
DOORS = (
    ("/workbench/", "workbench/index.html"),
    ("/manual/", "manual/index.html"),
)


def meta_map(html: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in META.finditer(html):
        out[m.group(1)] = m.group(2)
    return out


def json_ld(html: str) -> dict:
    m = re.search(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
        html,
        re.S,
    )
    if not m:
        return {}
    try:
        blob = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}
    return blob if isinstance(blob, dict) else {}


def card_fails(html: str, llms: str) -> list[str]:
    fails: list[str] = []
    tags = meta_map(html)
    og = tags.get("og:image", "")
    tw = tags.get("twitter:image", "")
    og_m = OG_URL.match(og)
    tw_m = OG_URL.match(tw)
    if tags.get("twitter:card") != CARD:
        fails.append("twitter:card is not " + CARD)
    if not og_m:
        fails.append("og:image is not " + HOST + "/" + OG_NAME + "?v=")
    if not tw_m:
        fails.append("twitter:image is not " + HOST + "/" + OG_NAME + "?v=")
    if og_m and tw_m and og != tw:
        fails.append("og:image and twitter:image disagree")
    ver = og_m.group(1) if og_m else ""
    if tags.get("og:image:width") != "1200" or tags.get("og:image:height") != "630":
        fails.append("og:image size is not 1200x630")
    if not tags.get("og:image:alt") or not tags.get("twitter:image:alt"):
        fails.append("og/twitter image alt is missing")
    if not HITS.search(html):
        fails.append("hello hits snippet missing slug instar")

    ld = json_ld(html)
    if not ld:
        fails.append("hello JSON-LD is missing")
    else:
        image = str(ld.get("image") or "")
        sw = str(ld.get("softwareVersion") or "")
        if image != og:
            fails.append("JSON-LD image disagrees with og:image")
        if ver and sw != ver:
            fails.append("JSON-LD softwareVersion disagrees with og.jpg?v=")

    lm = VER.search(llms)
    if not lm:
        fails.append("public/llms.txt has no Version line")
    elif ver and lm.group(1) != ver:
        fails.append("llms.txt Version disagrees with og.jpg?v=")
    return fails


def door_card_fails(rel: str, html: str, ver: str, want_url: str) -> list[str]:
    fails: list[str] = []
    tags = meta_map(html)
    og = tags.get("og:image", "")
    tw = tags.get("twitter:image", "")
    og_m = OG_URL.match(og)
    tw_m = OG_URL.match(tw)
    if tags.get("twitter:card") != CARD:
        fails.append(rel + " twitter:card is not " + CARD)
    if not og_m:
        fails.append(rel + " og:image is not " + HOST + "/" + OG_NAME + "?v=")
    elif og_m.group(1) != ver:
        fails.append(rel + " og.jpg?v= disagrees with hello")
    if not tw_m:
        fails.append(rel + " twitter:image is not " + HOST + "/" + OG_NAME + "?v=")
    if og_m and tw_m and og != tw:
        fails.append(rel + " og:image and twitter:image disagree")
    if tags.get("og:url") != want_url:
        fails.append(rel + " og:url is not " + want_url)
    if not tags.get("og:title") or not tags.get("og:description"):
        fails.append(rel + " missing og title or description")
    if not tags.get("twitter:title") or not tags.get("twitter:description"):
        fails.append(rel + " missing twitter title or description")
    return fails


def house_version_fails(ver: str) -> list[str]:
    fails: list[str] = []
    if not ver:
        return fails
    puzzle = PUB / "js" / "puzzle.js"
    sw = PUB / "sw.js"
    readme = ROOT / "README.md"
    if puzzle.is_file():
        pv = PUZZLE_V.search(puzzle.read_text(encoding="utf-8"))
        if not pv or pv.group(1) != ver:
            fails.append("puzzle.js v disagrees with og.jpg?v=")
    else:
        fails.append("public/js/puzzle.js is missing")
    if sw.is_file():
        cv = SW_CACHE.search(sw.read_text(encoding="utf-8"))
        if not cv or cv.group(1) != ver:
            fails.append("sw.js CACHE disagrees with og.jpg?v=")
    else:
        fails.append("public/sw.js is missing")
    if readme.is_file():
        if "v" + ver not in readme.read_text(encoding="utf-8"):
            fails.append("README.md missing v" + ver)
    else:
        fails.append("README.md is missing")
    return fails


def jpeg_ok(path: Path) -> bool:
    try:
        head = path.read_bytes()[:3]
    except OSError:
        return False
    return head == b"\xff\xd8\xff"


def scan_hello() -> list[str]:
    fails: list[str] = []
    og = PUB / OG_NAME
    if not og.is_file():
        fails.append("public/og.jpg is missing")
    elif not jpeg_ok(og):
        fails.append("public/og.jpg is not a JPEG")
    hello = PUB / "index.html"
    llms = PUB / "llms.txt"
    if not hello.is_file():
        fails.append("public/index.html is missing")
        return fails
    if not llms.is_file():
        fails.append("public/llms.txt is missing")
        return fails
    hello_html = hello.read_text(encoding="utf-8")
    llms_text = llms.read_text(encoding="utf-8")
    fails.extend(card_fails(hello_html, llms_text))
    tags = meta_map(hello_html)
    og_m = OG_URL.match(tags.get("og:image", ""))
    ver = og_m.group(1) if og_m else ""
    for url, rel in DOORS:
        path = PUB / rel
        if not path.is_file():
            fails.append("public/" + rel + " is missing")
            continue
        fails.extend(
            door_card_fails(rel, path.read_text(encoding="utf-8"), ver, HOST + url)
        )
    fails.extend(house_version_fails(ver))
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    good_html = (
        '<meta property="og:image" content="' + HOST + "/" + OG_NAME + '?v=1.1.1">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        '<meta property="og:image:alt" content="wing">\n'
        '<meta name="twitter:card" content="' + CARD + '">\n'
        '<meta name="twitter:image" content="' + HOST + "/" + OG_NAME + '?v=1.1.1">\n'
        '<meta name="twitter:image:alt" content="wing">\n'
        '<script type="application/ld+json">'
        '{"softwareVersion":"1.1.1","image":"' + HOST + "/" + OG_NAME + '?v=1.1.1"}'
        "</script>\n"
        '<script src="https://hits.jonbailey.xyz/c.js" data-site="instar"></script>\n'
    )
    if card_fails(good_html, "Version: 1.1.1\n"):
        fails.append("honest hello card flagged")
    bad = good_html.replace("?v=1.1.1", "?v=9.9.9", 1)
    if not card_fails(bad, "Version: 1.1.1\n"):
        fails.append("og/twitter version drift not flagged")
    if not card_fails(good_html, "Version: 0.0.0\n"):
        fails.append("llms version drift not flagged")
    no_card = good_html.replace(CARD, "summary")
    if not card_fails(no_card, "Version: 1.1.1\n"):
        fails.append("wrong twitter:card not flagged")
    door_html = (
        '<meta property="og:image" content="' + HOST + "/" + OG_NAME + '?v=1.1.1">\n'
        '<meta name="twitter:card" content="' + CARD + '">\n'
        '<meta name="twitter:image" content="' + HOST + "/" + OG_NAME + '?v=1.1.1">\n'
        '<meta property="og:url" content="' + HOST + '/workbench/">\n'
        '<meta property="og:title" content="Workbench">\n'
        '<meta property="og:description" content="lab">\n'
        '<meta name="twitter:title" content="Workbench">\n'
        '<meta name="twitter:description" content="lab">\n'
    )
    if door_card_fails("workbench/index.html", door_html, "1.1.1", HOST + "/workbench/"):
        fails.append("honest workbench card flagged")
    if not door_card_fails(
        "workbench/index.html",
        door_html.replace("?v=1.1.1", "?v=9.9.9"),
        "1.1.1",
        HOST + "/workbench/",
    ):
        fails.append("workbench version drift not flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("TWEET CARD SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    fails = scan_hello()
    if fails:
        print("TWEET CARD FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("TWEET CARD OK")
    print("hello og.jpg?v= , tweet card, JSON-LD, llms.txt, door cards, and house versions agree.")
    print("This is not a decipherment. No version was bumped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
