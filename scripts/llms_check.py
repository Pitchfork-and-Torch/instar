# INSTAR llms.txt check. ASCII. No spoilers. No decipherment.
# Run from repo root: python3 scripts/llms_check.py
#
# Agents read public/llms.txt. Cooks who edit that card can drop
# the live host, hide the public doors, or claim a Liber Primus
# break. This script does not fetch and does not name a molt
# answer. It fails when the machine-readable school card drifted:
#   - Version / Live / Workbench / Manual lines are missing
#   - a listed URL is off-host or an onion
#   - the not-a-hidden-service / unsolved banner is gone
#   - solve-claim copy appears
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import cook_guard as guard  # noqa: E402

PUB = ROOT / "public"
LLMS = PUB / "llms.txt"
HOST = "https://instar.jonbailey.xyz"
VER = re.compile(r"^(?:[\-\*]\s*)?Version:\s*(\S+)\s*$", re.M)
LIVE = re.compile(r"^(?:[\-\*]\s*)?Live:\s*(\S+)\s*$", re.M)
WORK = re.compile(r"^(?:[\-\*]\s*)?Workbench:\s*(\S+)\s*$", re.M)
MANUAL = re.compile(r"^(?:[\-\*]\s*)?Manual:\s*(\S+)\s*$", re.M)
ABS_URL = re.compile(r"https?://[^\s)>]+")
VER_OK = re.compile(r"^[0-9]+(?:\.[0-9]+)*$")


def href_kind(href: str) -> str:
    extra = guard.unknown_onions(href, guard.teaching_onions())
    if extra or ".onion" in href.lower():
        return "onion"
    if href.startswith(HOST + "/") or href == HOST or href == HOST + "/":
        return "host"
    return "off-host"


def scan_llms(text: str) -> list[str]:
    fails: list[str] = []
    vm = VER.search(text)
    if not vm or not VER_OK.match(vm.group(1)):
        fails.append("llms.txt missing a Version line")
    want = {
        "Live": (LIVE, HOST + "/"),
        "Workbench": (WORK, HOST + "/workbench/"),
        "Manual": (MANUAL, HOST + "/manual/"),
    }
    for label, (rx, url) in want.items():
        m = rx.search(text)
        if not m:
            fails.append("llms.txt missing " + label + " line")
        elif m.group(1) != url:
            fails.append("llms.txt " + label + " is not " + url)
    low = text.lower()
    if "not a hidden service" not in low:
        fails.append("llms.txt missing the not-a-hidden-service banner")
    if "unsolved" not in low:
        fails.append("llms.txt missing the unsolved banner")
    if guard.find_solve_claims(text):
        fails.append("llms.txt claims a Liber Primus break")
    extra = guard.unknown_onions(text, guard.teaching_onions())
    if extra:
        fails.append("llms.txt published a new onion")
    for href in ABS_URL.findall(text):
        kind = href_kind(href.rstrip(".,;"))
        if kind == "onion":
            fails.append("llms.txt link is an onion (do not publish onions)")
        elif kind == "off-host":
            fails.append("llms.txt link is off-host")
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    honest = (
        "Version: 1.1.1\n"
        "Live: " + HOST + "/\n"
        "Workbench: " + HOST + "/workbench/\n"
        "Manual: " + HOST + "/manual/\n"
        "Not a hidden service. Liber Primus pages remain unsolved here.\n"
    )
    if scan_llms(honest):
        fails.append("honest llms.txt flagged")
    if not scan_llms(honest.replace("Version: 1.1.1\n", "")):
        fails.append("missing Version not flagged")
    if not any(
        "Live is not" in x
        for x in scan_llms(honest.replace(HOST + "/", "https://example.com/", 1))
    ):
        fails.append("off-host Live not flagged")
    onion = honest + "see http://" + ("a" * 16) + ".onion/\n"
    if not any("onion" in x for x in scan_llms(onion)):
        fails.append("onion link not flagged")
    if not scan_llms(honest.replace("unsolved", "open")):
        fails.append("missing unsolved banner not flagged")
    return fails


def main() -> int:
    fails = self_check()
    if fails:
        print("LLMS SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    if not LLMS.is_file():
        print("LLMS FAIL", file=sys.stderr)
        print("  public/llms.txt is missing", file=sys.stderr)
        return 1
    fails = scan_llms(LLMS.read_text(encoding="utf-8"))
    if fails:
        print("LLMS FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("LLMS OK")
    print("llms.txt still names the public doors on-host, and stays unsolved.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
