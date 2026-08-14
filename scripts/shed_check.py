# INSTAR shed check. ASCII. No spoilers printed. No decipherment.
# Run from repo root: python3 scripts/shed_check.py
#
# After the cook guard, the next honest habit is a public-safe school
# gate. CI can run this without the secret journal. It does not invert
# a digest, fetch a hidden service, or name a molt answer. It fails
# when the public school is about to drift:
#   - cook_guard, page56 lab, unit lab, tweet card, precache, headers, listing, page-lab contract, door, cook map, manifest, or EN-only no longer hold
#   - browser and CLI page-56 labs disagree
#   - a required public file is missing
#   - a new magnet / IPFS / Freenet / I2P locator appears
#   - public HTML/JS/CSS picks up fancy dashes or smart quotes
#   - a hits snippet loses slug instar, or the hello tweet card drifts
#   - README or AGENTS.md claims a Liber Primus / Cicada break
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import cook_guard as guard  # noqa: E402
import page56_lab as lab  # noqa: E402

PUB = ROOT / "public"
HOUSE_SUFFIX = {".html", ".js", ".css", ".txt", ".xml", ".webmanifest", ".md"}
HASH_GATES = ("nymph", "soil", "song", "prime", "liber", "final")
PUBLIC_PATHS = [
    "index.html",
    "nymph/index.html",
    "soil/index.html",
    "tunnel/index.html",
    "song/index.html",
    "prime/index.html",
    "liber/index.html",
    "emerge/index.html",
    "brood/index.html",
    "husk/index.html",
    "workbench/index.html",
    "manual/index.html",
    "js/page56.js",
    "js/puzzle.js",
    "js/core.js",
    "og.jpg",
    "llms.txt",
    "static/clutch.txt",
    "library/soil-journal.txt",
    "media/wing.png",
    "media/emergence.wav",
]

# Teaching locators already printed by the page 56 lab. Not new doors.
MAGNET = re.compile(r"magnet:\?xt=urn:btih:[a-fA-F0-9]{40}", re.I)
IPFS_URI = re.compile(r"\bipfs://[a-zA-Z0-9]+", re.I)
IPFS_PATH = re.compile(r"/ipfs/[a-zA-Z0-9]+")
IPFS_CIDV1 = re.compile(r"\bbafy[a-z2-7]{20,}\b", re.I)
FREENET_KEY = re.compile(r"\b(?:CHK|SSK|USK|KSK)@[A-Za-z0-9~.-]+")
I2P_B32 = re.compile(r"\b[a-z2-7]{52}\.b32\.i2p\b", re.I)
FANCY = re.compile(r"[\u2013\u2014\u2018\u2019\u201c\u201d]")
JS_STR = re.compile(r'const\s+([A-Z0-9_]+)\s*=\s*"([^"]+)"')
JS_ARR = re.compile(r"const\s+([A-Z0-9_]+)\s*=\s*\[(.*?)\]", re.S)


def hits_slug_missing(text: str) -> bool:
    return "hits.jonbailey.xyz/c.js" in text and 'data-site="instar"' not in text


def teaching_magnets() -> set[str]:
    return {lab.magnet_btih(lab.first8(lab.LINES)).lower()}


def find_locators(text: str) -> dict[str, set[str]]:
    found = {
        "magnet": {m.group(0).lower() for m in MAGNET.finditer(text)},
        "ipfs": set(),
        "freenet": {m.group(0) for m in FREENET_KEY.finditer(text)},
        "i2p": {m.group(0).lower() for m in I2P_B32.finditer(text)},
    }
    for rx in (IPFS_URI, IPFS_PATH, IPFS_CIDV1):
        found["ipfs"].update(m.group(0) for m in rx.finditer(text))
    return found


def unknown_locators(text: str, magnets: set[str]) -> list[str]:
    hits = find_locators(text)
    extra = []
    if hits["magnet"] - magnets:
        extra.append("magnet")
    if hits["ipfs"]:
        extra.append("ipfs")
    if hits["freenet"]:
        extra.append("freenet")
    if hits["i2p"]:
        extra.append("i2p")
    return extra


def parse_page56_js(text: str) -> dict[str, object]:
    strs = {m.group(1): m.group(2) for m in JS_STR.finditer(text)}
    arrs: dict[str, list[str]] = {}
    for m in JS_ARR.finditer(text):
        arrs[m.group(1)] = re.findall(r'"([^"]+)"', m.group(2))
    return {
        "HEX": strs.get("HEX", ""),
        "LINES": arrs.get("LINES", []),
        "ONION_V2": strs.get("ONION_V2", ""),
    }


def parity_fails(js: dict[str, object]) -> list[str]:
    fails: list[str] = []
    hex_s = str(js.get("HEX") or "")
    lines = list(js.get("LINES") or [])
    onion = str(js.get("ONION_V2") or "")
    if hex_s != lab.HEX:
        fails.append("page56 HEX drift (browser vs CLI)")
    if lines != lab.LINES:
        fails.append("page56 LINES drift (browser vs CLI)")
    if onion != lab.ONION_V2:
        fails.append("page56 onion constant drift (browser vs CLI)")
    if hex_s and lines:
        if lab.first8(lines) != lab.first8(lab.LINES):
            fails.append("page56 extract drift (browser vs CLI)")
        if lab.after8(lines) != lab.after8(lab.LINES):
            fails.append("page56 leftover drift (browser vs CLI)")
    return fails


def puzzle_blob() -> dict:
    text = (PUB / "js" / "puzzle.js").read_text(encoding="utf-8")
    m = re.search(r"window\.INSTAR_PUZZLE\s*=\s*(\{.*\})\s*;?\s*$", text, re.S)
    if not m:
        raise ValueError("puzzle.js has no INSTAR_PUZZLE object")
    return json.loads(m.group(1))


def run_tool(args: list[str], token: str) -> list[str]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return [args[-1] + " could not start: " + type(exc).__name__]
    if proc.returncode == 0 and token in (proc.stdout or ""):
        return []
    err = (proc.stderr or proc.stdout or "no output").strip().splitlines()
    head = err[0] if err else "no output"
    return [Path(args[-1]).name + " failed: " + head]


def scan_tree() -> list[str]:
    fails: list[str] = []
    magnets = teaching_magnets()

    for rel in PUBLIC_PATHS:
        path = PUB / rel
        if not path.is_file():
            fails.append("missing public/" + rel)

    wing = PUB / "media" / "wing.png"
    if wing.is_file() and b"INSTAR-TAIL" not in wing.read_bytes():
        fails.append("public/media/wing.png is missing its strings tail")
    wav = PUB / "media" / "emergence.wav"
    if wav.is_file() and wav.stat().st_size < 10000:
        fails.append("public/media/emergence.wav is too small to be a spectrogram lesson")

    js_path = PUB / "js" / "page56.js"
    if js_path.is_file():
        fails.extend(parity_fails(parse_page56_js(js_path.read_text(encoding="utf-8"))))

    try:
        puzzle = puzzle_blob()
    except (OSError, ValueError, json.JSONDecodeError):
        fails.append("public/js/puzzle.js is not a readable puzzle object")
        puzzle = {}
    hashes = puzzle.get("hashes") if isinstance(puzzle.get("hashes"), dict) else {}
    if "answers" in puzzle:
        fails.append("public/js/puzzle.js dumps an answers object")
    for name in HASH_GATES:
        got = hashes.get(name, "")
        if not re.fullmatch(r"[a-f0-9]{64}", str(got)):
            fails.append("public/js/puzzle.js missing hashed gate " + name)

    for path in guard.tracked_paths():
        if not path.is_file() or not guard.is_text(path):
            continue
        name = guard.rel(path)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        extra = unknown_locators(text, magnets)
        if extra:
            fails.append(name + ": new locator (" + ", ".join(sorted(set(extra))) + ")")
        if name in ("README.md", "AGENTS.md"):
            claims = guard.find_solve_claims(text)
            if claims:
                fails.append(name + ": solve-claim copy (school, not a break)")
        if not name.startswith("public/") or name.startswith("public/fonts/"):
            continue
        if path.suffix.lower() in HOUSE_SUFFIX and FANCY.search(text):
            fails.append(name + ": fancy dash or smart quote (ASCII dashes in public copy)")
        if hits_slug_missing(text):
            fails.append(name + ": hits snippet missing slug instar")
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    magnets = teaching_magnets()
    if len(magnets) != 1:
        fails.append("teaching magnet allowlist is empty")
    teach = next(iter(magnets)) if magnets else ""
    if teach and unknown_locators(teach, magnets):
        fails.append("teaching magnet flagged")
    fake = "magnet:?xt=urn:btih:" + ("ab" * 20)
    if "magnet" not in unknown_locators("see " + fake, magnets):
        fails.append("unknown magnet not flagged")
    if unknown_locators("IPFS CIDv0 wants SHA-256. Freenet CHK is not a raw dump.", magnets):
        fails.append("locator prose flagged as a door")
    ipfs_fake = "ipfs://" + "bafy" + "testcidvaluehereplease"
    if "ipfs" not in unknown_locators("open " + ipfs_fake, magnets):
        fails.append("ipfs uri detector miss")
    if "i2p" not in unknown_locators("host " + ("a" * 52) + ".b32.i2p", magnets):
        fails.append("i2p detector miss")
    js = parse_page56_js((PUB / "js" / "page56.js").read_text(encoding="utf-8"))
    if parity_fails(js):
        fails.append("live page56 labs already disagree")
    bad = dict(js)
    bad["HEX"] = "00" * 64
    if not parity_fails(bad):
        fails.append("parity detector miss")
    if not FANCY.search("hello\u2014world"):
        fails.append("fancy-dash detector miss")
    if FANCY.search("ASCII dash - is fine"):
        fails.append("ASCII dash flagged")
    if guard.find_solve_claims("The preimage is still unsolved. This is a school."):
        fails.append("honest unsolved copy flagged as a claim")
    if not guard.find_solve_claims("we solved liber primus yesterday"):
        fails.append("solve-claim detector miss")
    if hits_slug_missing("script-src https://hits.jonbailey.xyz"):
        fails.append("CSP hits host flagged as a snippet")
    if not hits_slug_missing('<script src="https://hits.jonbailey.xyz/c.js"></script>'):
        fails.append("hits snippet without slug not flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("SHED CHECK SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    fails = run_tool([sys.executable, str(SCRIPTS / "cook_guard.py")], "COOK GUARD OK")
    fails += run_tool([sys.executable, str(SCRIPTS / "page56_lab.py")], "PAGE56 OK")
    fails += run_tool(["node", str(SCRIPTS / "unit_lab.js")], "UNIT OK")
    fails += run_tool(
        [sys.executable, str(SCRIPTS / "ensure_tweet_card.py")], "TWEET CARD OK"
    )
    fails += run_tool(
        [sys.executable, str(SCRIPTS / "precache_check.py")], "PRECACHE OK"
    )
    fails += run_tool(
        [sys.executable, str(SCRIPTS / "headers_check.py")], "HEADERS OK"
    )
    fails += run_tool(
        [sys.executable, str(SCRIPTS / "listing_check.py")], "LISTING OK"
    )
    fails += run_tool(
        [sys.executable, str(SCRIPTS / "page_lab_contract.py")], "PAGE LAB CONTRACT OK"
    )
    fails += run_tool(
        [sys.executable, str(SCRIPTS / "door_check.py")], "DOOR OK"
    )
    fails += run_tool(
        [sys.executable, str(SCRIPTS / "cook_map.py")], "COOK MAP OK"
    )
    fails += run_tool(
        [sys.executable, str(SCRIPTS / "manifest_check.py")], "MANIFEST OK"
    )
    fails += run_tool(
        [sys.executable, str(SCRIPTS / "en_check.py")], "EN OK"
    )
    fails += scan_tree()
    if fails:
        print("SHED CHECK FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("SHED CHECK OK")
    print("public school holds: cook guard, page56 lab, unit lab, tweet card, precache, headers, listing, page-lab contract, door, cook map, manifest, EN,")
    print("lab parity, required files, no new locator, house rails, no solve claim.")
    print("This is not a decipherment. The secret journal was not opened.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
