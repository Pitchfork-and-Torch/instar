# INSTAR cook-map check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/cook_map.py
#
# After ten public-safe gates, cooks need a map that cannot rot.
# This script does not invert a digest or name a molt answer. It
# fails when scripts/COOK.md drifts off the live commands.
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import cook_guard as guard  # noqa: E402

MAP = SCRIPTS / "COOK.md"
GATES = (
    "shed_check.py",
    "cook_guard.py",
    "page56_lab.py",
    "unit_lab.js",
    "ensure_tweet_card.py",
    "precache_check.py",
    "headers_check.py",
    "listing_check.py",
    "page_lab_contract.py",
    "door_check.py",
    "manifest_check.py",
    "en_check.py",
    "canon_check.py",
    "llms_check.py",
    "icon_check.py",
    "deploy.ps1",
)


def scan_map(text: str) -> list[str]:
    fails: list[str] = []
    if "not a decipherment" not in text.lower() and "not a cicada solve" not in text.lower():
        fails.append("scripts/COOK.md missing the school-not-a-solve banner")
    if "do not publish onions" not in text.lower():
        fails.append("scripts/COOK.md missing the no-onion rule")
    extra = guard.unknown_onions(text, guard.teaching_onions())
    if extra:
        fails.append("scripts/COOK.md: new onion host (do not publish onions)")
    claims = guard.find_solve_claims(text)
    if claims:
        fails.append("scripts/COOK.md: solve-claim copy (school, not a break)")
    for name in GATES:
        if name not in text:
            fails.append("scripts/COOK.md missing " + name)
        path = ROOT / "scripts" / name if name != "deploy.ps1" else ROOT / name
        if name == "deploy.ps1":
            path = ROOT / "deploy.ps1"
        if not path.is_file():
            fails.append(name + " is missing on disk")
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    body = "A school. Not a Cicada solve.\nDo not publish onions.\nThis is not a decipherment.\n"
    body += "\n".join(GATES) + "\n"
    if scan_map(body):
        fails.append("honest cook map flagged")
    if not scan_map(body.replace("shed_check.py", "missing_gate.py")):
        fails.append("missing gate name not flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("COOK MAP SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    if not MAP.is_file():
        print("COOK MAP FAIL", file=sys.stderr)
        print("  scripts/COOK.md is missing", file=sys.stderr)
        return 1
    fails = scan_map(MAP.read_text(encoding="utf-8"))
    if fails:
        print("COOK MAP FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("COOK MAP OK")
    print("scripts/COOK.md still names every public-safe gate.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
