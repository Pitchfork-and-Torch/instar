# INSTAR page-lab contract. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/page_lab_contract.py
#
# Future page*_lab.py files stay local and honest. This script does
# not invert a digest, fetch a hidden service, or name a molt answer.
# It fails when a page lab drifted:
#   - no scripts/page*_lab.py
#   - a lab imports or calls a network client
#   - a lab never prints a PAGE<n> OK token
#   - a lab drops the no-preimage banner, or claims a Liber break
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import cook_guard as guard  # noqa: E402

LAB_GLOB = "page*_lab.py"
OK_TOKEN = re.compile(r'PAGE\d+\s+OK')
PREIMAGE = re.compile(r"no preimage|not a preimage", re.I)
NET_IMPORT = re.compile(
    r"^\s*(?:import\s+(?:requests|httpx|aiohttp|urllib3|http\.client)|"
    r"from\s+urllib(?:\.request)?\s+import|"
    r"from\s+http\.client\s+import)",
    re.M,
)
NET_CALL = re.compile(
    r"\b(?:urlopen|urlretrieve|requests\.(?:get|post|put|head)|"
    r"httpx\.(?:get|post)|socket\.create_connection)\s*\("
)


def lab_paths() -> list[Path]:
    return sorted(SCRIPTS.glob(LAB_GLOB))


def scan_lab(name: str, text: str) -> list[str]:
    fails: list[str] = []
    if NET_IMPORT.search(text):
        fails.append(name + ": network import (page labs stay local)")
    if NET_CALL.search(text):
        fails.append(name + ": network call (do not fetch a hidden service)")
    if not OK_TOKEN.search(text):
        fails.append(name + ": missing PAGE<n> OK token")
    if not PREIMAGE.search(text):
        fails.append(name + ": missing no-preimage banner")
    claims = guard.find_solve_claims(text)
    if claims:
        fails.append(name + ": solve-claim copy (school, not a break)")
    return fails


def scan_tree() -> list[str]:
    paths = lab_paths()
    if not paths:
        return ["no scripts/page*_lab.py (page 56 lab is the template)"]
    fails: list[str] = []
    names = {p.name for p in paths}
    if "page56_lab.py" not in names:
        fails.append("scripts/page56_lab.py is missing")
    for path in paths:
        fails.extend(scan_lab(path.name, path.read_text(encoding="utf-8")))
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    good = (
        "# Page 99 lab. No preimage search.\n"
        'print("PAGE99 OK")\n'
    )
    if scan_lab("good.py", good):
        fails.append("honest page lab flagged")
    if not scan_lab("net.py", good + "import requests\n"):
        fails.append("network import not flagged")
    if not scan_lab("fetch.py", good + "urlopen('https://example')\n"):
        fails.append("urlopen not flagged")
    if not scan_lab("bare.py", "print('hello')\n"):
        fails.append("missing OK token not flagged")
    if not scan_lab("claim.py", good + "we solved liber primus yesterday\n"):
        fails.append("solve-claim not flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("PAGE LAB CONTRACT SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    fails = scan_tree()
    if fails:
        print("PAGE LAB CONTRACT FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("PAGE LAB CONTRACT OK")
    print("page labs stay local, print PAGE<n> OK, and do not claim a break.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
