# INSTAR seal / icon check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/icon_check.py
#
# Public doors share one seal. Cooks who copy a door can drop the
# favicon, point apple-touch at a missing file, or let the manifest
# icon drift. This script does not fetch and does not name a molt
# answer. It fails when the seal house drifted:
#   - public/media/seal.jpg is missing or not a JPEG
#   - a public door lost rel=icon or apple-touch-icon
#   - an icon href is not /media/seal.jpg
#   - the webmanifest icon src drifted
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
SEAL = "/media/seal.jpg"
SEAL_PATH = PUB / "media" / "seal.jpg"
MANIFEST = PUB / "manifest.webmanifest"
DOORS = (
    ("/", "index.html"),
    ("/workbench/", "workbench/index.html"),
    ("/manual/", "manual/index.html"),
)
LINK = re.compile(r"<link\b[^>]*>", re.I)
REL = re.compile(r'\brel="([^"]+)"', re.I)
HREF = re.compile(r'\bhref="([^"]+)"', re.I)


def jpeg_ok(path: Path) -> bool:
    try:
        head = path.read_bytes()[:3]
    except OSError:
        return False
    return head == b"\xff\xd8\xff"


def link_hrefs(text: str, want: str) -> list[str]:
    out: list[str] = []
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


def scan_door(url: str, html: str) -> list[str]:
    fails: list[str] = []
    icons = link_hrefs(html, "icon")
    apples = link_hrefs(html, "apple-touch-icon")
    if not icons:
        fails.append(url + " missing rel=icon")
    for href in icons:
        if href != SEAL:
            fails.append(url + " icon is not " + SEAL)
    if not apples:
        fails.append(url + " missing apple-touch-icon")
    for href in apples:
        if href != SEAL:
            fails.append(url + " apple-touch-icon is not " + SEAL)
    return fails


def scan_manifest(text: str) -> list[str]:
    fails: list[str] = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return ["public/manifest.webmanifest is not JSON"]
    if not isinstance(data, dict):
        return ["public/manifest.webmanifest is not JSON"]
    icons = data.get("icons")
    if not isinstance(icons, list) or not icons:
        fails.append("manifest has no icons")
        return fails
    for icon in icons:
        if not isinstance(icon, dict):
            fails.append("manifest icon is not an object")
            continue
        src = str(icon.get("src") or "")
        if src != SEAL:
            fails.append("manifest icon src is not " + SEAL)
    return fails


def scan_public() -> list[str]:
    fails: list[str] = []
    if not SEAL_PATH.is_file():
        fails.append("public/media/seal.jpg is missing")
    elif not jpeg_ok(SEAL_PATH):
        fails.append("public/media/seal.jpg is not a JPEG")
    for url, rel in DOORS:
        path = PUB / rel
        if not path.is_file():
            fails.append("public door missing: " + url)
            continue
        fails += scan_door(url, path.read_text(encoding="utf-8"))
    if not MANIFEST.is_file():
        fails.append("public/manifest.webmanifest is missing")
    else:
        fails += scan_manifest(MANIFEST.read_text(encoding="utf-8"))
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    door = (
        '<link rel="icon" href="/media/seal.jpg">\n'
        '<link rel="apple-touch-icon" href="/media/seal.jpg">\n'
    )
    if scan_door("/", door):
        fails.append("honest door flagged")
    if not scan_door("/", "<html lang=\"en\">\n"):
        fails.append("missing icon not flagged")
    if not any(
        "icon is not" in x
        for x in scan_door("/", '<link rel="icon" href="/favicon.ico">\n')
    ):
        fails.append("wrong icon href not flagged")
    man = '{"icons":[{"src":"/media/seal.jpg","sizes":"512x512"}]}'
    if scan_manifest(man):
        fails.append("honest manifest flagged")
    if not scan_manifest('{"icons":[{"src":"/other.jpg"}]}'):
        fails.append("wrong manifest icon not flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("ICON SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    fails = scan_public()
    if fails:
        print("ICON FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("ICON OK")
    print("public doors and the webmanifest still share /media/seal.jpg.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
