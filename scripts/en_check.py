# INSTAR EN-only check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/en_check.py
#
# i18n is paused. Cooks who add a page can leave lang off, add
# hreflang, or stand up a locale folder. This script does not
# translate and does not name a molt answer. It fails when the
# English-only house drifted:
#   - a public HTML page is missing lang="en"
#   - hreflang or og:locale:alternate appears
#   - og:locale is present and not en_US
#   - hello lost og:locale
#   - a locale / i18n directory landed under public/
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
HTML_TAG = re.compile(r"<html\b([^>]*)>", re.I)
LANG_ATTR = re.compile(r"""\blang\s*=\s*["']([^"']+)["']""", re.I)
HREFLANG = re.compile(r"\bhreflang\s*=", re.I)
OG_LOCALE = re.compile(
    r'<meta\s+property="og:locale"\s+content="([^"]+)"\s*/?>', re.I
)
OG_LOCALE_ALT = re.compile(r'<meta\s+property="og:locale:alternate"', re.I)
LOCALE_DIRS = {
    "i18n",
    "locales",
    "locale",
    "lang",
    "langs",
    "en",
    "en-us",
    "en-gb",
    "es",
    "fr",
    "de",
    "it",
    "pt",
    "ja",
    "zh",
    "ko",
    "ru",
    "ar",
    "nl",
    "pl",
    "sv",
}


def html_rel(path: Path) -> str:
    return path.relative_to(PUB).as_posix()


def scan_html(rel: str, text: str, require_og: bool) -> list[str]:
    fails: list[str] = []
    tag = HTML_TAG.search(text)
    if not tag:
        fails.append(rel + " missing <html>")
        return fails
    lang = LANG_ATTR.search(tag.group(1))
    if not lang:
        fails.append(rel + " missing lang=\"en\"")
    elif lang.group(1).lower() != "en":
        fails.append(rel + " lang is not en")
    if HREFLANG.search(text):
        fails.append(rel + " has hreflang (i18n pause)")
    if OG_LOCALE_ALT.search(text):
        fails.append(rel + " has og:locale:alternate (i18n pause)")
    locales = [m.group(1) for m in OG_LOCALE.finditer(text)]
    if require_og and not locales:
        fails.append(rel + " missing og:locale en_US")
    for loc in locales:
        if loc != "en_US":
            fails.append(rel + " og:locale is not en_US")
    return fails


def locale_dirs(names: list[str]) -> list[str]:
    fails: list[str] = []
    for name in names:
        if name.lower() in LOCALE_DIRS:
            fails.append("locale directory under public/: " + name)
    return fails


def scan_public() -> list[str]:
    fails: list[str] = []
    pages = sorted(PUB.rglob("*.html"))
    if not pages:
        fails.append("no public HTML pages")
        return fails
    for path in pages:
        rel = html_rel(path)
        require_og = rel == "index.html"
        fails += scan_html(rel, path.read_text(encoding="utf-8"), require_og)
    names = [p.name for p in PUB.iterdir() if p.is_dir()]
    fails += locale_dirs(names)
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    hello = (
        '<html lang="en">\n'
        '<meta property="og:locale" content="en_US">\n'
    )
    chamber = '<html lang="en">\n<title>chamber</title>\n'
    if scan_html("index.html", hello, True):
        fails.append("honest hello flagged")
    if scan_html("husk/index.html", chamber, False):
        fails.append("honest chamber flagged")
    if not scan_html("x.html", '<html lang="fr">\n', False):
        fails.append("non-en lang not flagged")
    if not scan_html("x.html", "<html>\n", False):
        fails.append("missing lang not flagged")
    if not any(
        "hreflang" in x
        for x in scan_html(
            "x.html",
            '<html lang="en">\n<link rel="alternate" hreflang="es" href="/es/">\n',
            False,
        )
    ):
        fails.append("hreflang not flagged")
    if not any(
        "og:locale is not" in x
        for x in scan_html(
            "index.html",
            '<html lang="en">\n<meta property="og:locale" content="es_ES">\n',
            True,
        )
    ):
        fails.append("non-en og:locale not flagged")
    if not any(
        "missing og:locale" in x
        for x in scan_html("index.html", '<html lang="en">\n', True)
    ):
        fails.append("hello without og:locale not flagged")
    if not locale_dirs(["es", "workbench"]):
        fails.append("locale directory not flagged")
    if locale_dirs(["workbench", "husk", "manual"]):
        fails.append("school directory flagged as locale")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("EN SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    if not PUB.is_dir():
        print("EN FAIL", file=sys.stderr)
        print("  public/ is missing", file=sys.stderr)
        return 1
    fails = scan_public()
    if fails:
        print("EN FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("EN OK")
    print("public HTML stays English-only. i18n is still paused.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
