# INSTAR PWA manifest check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/manifest_check.py
#
# Cooks who edit install chrome can point start_url at a chamber,
# drop the hello manifest link, or lose the seal icon. This script
# does not fetch and does not name a molt answer. It fails when the
# install house drifted:
#   - name, start_url, scope, display, or lang is not the school
#   - an icon path is missing on disk
#   - a public door lost the manifest link or theme-color
#   - PRECACHE dropped /manifest.webmanifest
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import cook_guard as guard  # noqa: E402

PUB = ROOT / "public"
MANIFEST = PUB / "manifest.webmanifest"
SW = PUB / "sw.js"
DOORS = (
    ("/", "index.html"),
    ("/workbench/", "workbench/index.html"),
    ("/manual/", "manual/index.html"),
)
THEME = "#080705"
MANIFEST_URL = "/manifest.webmanifest"
LINK_RE = re.compile(
    r'<link\s+rel="manifest"\s+href="/manifest\.webmanifest"\s*/?>', re.I
)
THEME_RE = re.compile(
    r'<meta\s+name="theme-color"\s+content="([^"]+)"\s*/?>', re.I
)
PRECACHE_RE = re.compile(r"const PRECACHE\s*=\s*\[(.*?)\]\s*;", re.S)
ITEM_RE = re.compile(r'"(/[^"]*)"')


def parse_manifest(text: str) -> dict | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def public_file(url: str) -> Path:
    rel = url.lstrip("/")
    return PUB / rel


def precache_items(text: str) -> list[str]:
    lm = PRECACHE_RE.search(text)
    if not lm:
        return []
    return ITEM_RE.findall(lm.group(1))


def scan_manifest(data: dict, doors: dict[str, str], sw_text: str) -> list[str]:
    fails: list[str] = []
    if data.get("name") != "INSTAR" or data.get("short_name") != "INSTAR":
        fails.append("manifest name/short_name is not INSTAR")
    if data.get("start_url") != "/":
        fails.append("manifest start_url is not /")
    if data.get("scope") != "/":
        fails.append("manifest scope is not /")
    if data.get("display") != "standalone":
        fails.append("manifest display is not standalone")
    if data.get("lang") != "en":
        fails.append("manifest lang is not en")
    if str(data.get("theme_color", "")).lower() != THEME:
        fails.append("manifest theme_color drifted")
    if str(data.get("background_color", "")).lower() != THEME:
        fails.append("manifest background_color drifted")

    desc = str(data.get("description") or "")
    if not desc:
        fails.append("manifest description is empty")
    if guard.find_solve_claims(desc):
        fails.append("manifest description claims a Liber Primus break")
    extra = guard.unknown_onions(desc, guard.teaching_onions())
    if extra:
        fails.append("manifest description published a new onion")

    icons = data.get("icons")
    if not isinstance(icons, list) or not icons:
        fails.append("manifest has no icons")
    else:
        for icon in icons:
            if not isinstance(icon, dict):
                fails.append("manifest icon is not an object")
                continue
            src = str(icon.get("src") or "")
            if not src.startswith("/"):
                fails.append("manifest icon src is not a root path")
                continue
            if not public_file(src).is_file():
                fails.append("manifest icon missing on disk: " + src)
            if not icon.get("sizes"):
                fails.append("manifest icon missing sizes: " + src)

    for url, html in doors.items():
        if not LINK_RE.search(html):
            fails.append(url + " missing manifest link")
        tm = THEME_RE.search(html)
        if not tm or tm.group(1).lower() != THEME:
            fails.append(url + " theme-color does not match the manifest")

    if MANIFEST_URL not in precache_items(sw_text):
        fails.append("PRECACHE dropped " + MANIFEST_URL)
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    honest = {
        "name": "INSTAR",
        "short_name": "INSTAR",
        "description": "A school. Not a Cicada solve.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": THEME,
        "theme_color": THEME,
        "lang": "en",
        "icons": [
            {
                "src": "/media/seal.jpg",
                "sizes": "512x512",
                "type": "image/jpeg",
                "purpose": "any",
            }
        ],
    }
    door = (
        '<html lang="en">\n'
        '<meta name="theme-color" content="#080705">\n'
        '<link rel="manifest" href="/manifest.webmanifest">\n'
    )
    doors = {url: door for url, _rel in DOORS}
    sw = 'const PRECACHE = [\n  "/",\n  "/manifest.webmanifest",\n];\n'
    if scan_manifest(honest, doors, sw):
        fails.append("honest manifest flagged")
    bad_start = dict(honest)
    bad_start["start_url"] = "/husk/"
    if not scan_manifest(bad_start, doors, sw):
        fails.append("chamber start_url not flagged")
    bad_lang = dict(honest)
    bad_lang["lang"] = "fr"
    if not scan_manifest(bad_lang, doors, sw):
        fails.append("non-en lang not flagged")
    missing_icon = dict(honest)
    missing_icon["icons"] = [
        {"src": "/media/missing-seal.jpg", "sizes": "512x512"}
    ]
    if not any("missing on disk" in x for x in scan_manifest(missing_icon, doors, sw)):
        fails.append("missing icon not flagged")
    no_link = {url: '<html lang="en">\n' for url, _rel in DOORS}
    if not any("missing manifest link" in x for x in scan_manifest(honest, no_link, sw)):
        fails.append("missing door link not flagged")
    if not scan_manifest(honest, doors, 'const PRECACHE = ["/"];'):
        fails.append("PRECACHE drop not flagged")
    parsed = parse_manifest('{"name":"INSTAR"}')
    if not parsed or parsed.get("name") != "INSTAR":
        fails.append("manifest parser miss")
    if parse_manifest("{") is not None:
        fails.append("broken JSON not rejected")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("MANIFEST SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    if not MANIFEST.is_file():
        print("MANIFEST FAIL", file=sys.stderr)
        print("  public/manifest.webmanifest is missing", file=sys.stderr)
        return 1
    data = parse_manifest(MANIFEST.read_text(encoding="utf-8"))
    if data is None:
        print("MANIFEST FAIL", file=sys.stderr)
        print("  public/manifest.webmanifest is not JSON", file=sys.stderr)
        return 1
    doors: dict[str, str] = {}
    for url, rel in DOORS:
        path = PUB / rel
        if not path.is_file():
            print("MANIFEST FAIL", file=sys.stderr)
            print("  public door missing: " + url, file=sys.stderr)
            return 1
        doors[url] = path.read_text(encoding="utf-8")
    sw_text = SW.read_text(encoding="utf-8") if SW.is_file() else ""
    fails = scan_manifest(data, doors, sw_text)
    if fails:
        print("MANIFEST FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("MANIFEST OK")
    print("install chrome still points at hello, and every icon exists.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
