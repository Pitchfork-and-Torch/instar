# INSTAR page-cook guard. ASCII. No spoilers printed. No decipherment.
# Run from repo root: python3 scripts/cook_guard.py
#
# After the page 56 lab, the next honest habit is a gate on the tree
# itself. Future page cooks run this before a PR. It does not invert a
# digest, fetch a hidden service, or name a molt answer. It only fails
# when a cook is about to publish something the school must not ship:
#   - the local secret manifest
#   - a new onion host (the published dead page-56 v2 stays allowlisted)
#   - a credential or private-key shape
#   - a Liber Primus / Cicada solve claim in public copy
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_SUFFIX = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".wav",
    ".mp3",
    ".woff",
    ".woff2",
    ".otf",
    ".ttf",
    ".eot",
    ".ico",
    ".pdf",
    ".zip",
    ".wasm",
}
SECRET_MANIFEST = "scripts/_secret_manifest.json"

# v2 = 16 chars, v3 = 56 chars. Alphabet is RFC 4648 base32 without padding.
ONION_HOST = re.compile(r"\b([a-z2-7]{16}|[a-z2-7]{56})\.onion\b", re.I)
ONION_NEAR = re.compile(
    r"(?i)\bonion\b(?:\s+host|\s+v2|\s+v3)?[:\s=]+['\"]?([a-z2-7]{16}|[a-z2-7]{56})\b"
)
ONION_V3_QUOTED = re.compile(r"['\"]([a-z2-7]{56})['\"]", re.I)

PEM = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
AWS_KEY = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
GITHUB_PAT = re.compile(r"\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,})\b")
SLACK_TOK = re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")
STRIPE_LIVE = re.compile(r"\b[rs]k_live_[A-Za-z0-9]{10,}\b")

# Tight on purpose. "The preimage is still unsolved" must pass.
SOLVE_CLAIM = [
    re.compile(r"solved liber primus", re.I),
    re.compile(r"liber primus (is|has been) solved", re.I),
    re.compile(r"preimage is ['\"]?[a-f0-9]{8,}", re.I),
    re.compile(r"we (have )?(solved|cracked|broken) (page|liber|cicada)", re.I),
    re.compile(r"this (is|repo) (a |the )?(cicada )?solve\b", re.I),
    re.compile(r"decipherment of (page|liber primus)", re.I),
]


def teaching_onions() -> set[str]:
    """Hosts the school already teaches. Dead or ruled-out. Not doors."""
    lab_path = ROOT / "scripts" / "page56_lab.py"
    sys.path.insert(0, str(lab_path.parent))
    import page56_lab as lab

    derived = lab.onion_from_extract(lab.first8(lab.chunks(lab.HEX, 16)))
    return {lab.ONION_V2.lower(), derived.lower()}


def find_onion_hosts(text: str) -> set[str]:
    hosts: set[str] = set()
    for rx in (ONION_HOST, ONION_NEAR, ONION_V3_QUOTED):
        for m in rx.finditer(text):
            hosts.add(m.group(1).lower())
    return hosts


def unknown_onions(text: str, allow: set[str]) -> set[str]:
    return {h for h in find_onion_hosts(text) if h not in allow}


def find_secrets(text: str) -> list[str]:
    hits: list[str] = []
    if PEM.search(text):
        hits.append("private-key-pem")
    if AWS_KEY.search(text):
        hits.append("aws-access-key")
    if GITHUB_PAT.search(text):
        hits.append("github-token")
    if SLACK_TOK.search(text):
        hits.append("slack-token")
    if STRIPE_LIVE.search(text):
        hits.append("stripe-live-key")
    return hits


def find_solve_claims(text: str) -> list[str]:
    return [rx.pattern for rx in SOLVE_CLAIM if rx.search(text)]


def tracked_paths() -> list[Path]:
    try:
        raw = subprocess.check_output(
            ["git", "ls-files", "-z"],
            cwd=str(ROOT),
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return [
            p
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts
        ]
    out: list[Path] = []
    for chunk in raw.split(b"\0"):
        if not chunk:
            continue
        out.append(ROOT / chunk.decode("utf-8", errors="replace"))
    return out


def is_text(path: Path) -> bool:
    if path.suffix.lower() in SKIP_SUFFIX:
        return False
    try:
        if path.stat().st_size > 2_000_000:
            return False
    except OSError:
        return False
    return True


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def scan_tree(allow: set[str]) -> list[str]:
    fails: list[str] = []
    gi = ROOT / ".gitignore"
    if gi.is_file() and SECRET_MANIFEST not in gi.read_text(encoding="utf-8"):
        fails.append(".gitignore does not ignore " + SECRET_MANIFEST)

    tracked = tracked_paths()
    tracked_rel = {rel(p) for p in tracked}
    if SECRET_MANIFEST in tracked_rel:
        fails.append(SECRET_MANIFEST + " is tracked (local spoilers; do not commit)")

    clutch = ROOT / "public" / "static" / "clutch.txt"
    if clutch.is_file():
        first = clutch.read_text(encoding="utf-8").splitlines()[0].strip()
        if first.upper() == "THE FIRST GATE IS NYMPHED":
            fails.append("public/static/clutch.txt carries plaintext (keep the atbash)")

    puzzle = ROOT / "public" / "js" / "puzzle.js"
    if puzzle.is_file():
        body = puzzle.read_text(encoding="utf-8")
        if re.search(r"\banswers\s*[:=]\s*\{", body):
            fails.append("public/js/puzzle.js dumps an answers object")

    for path in tracked:
        if not path.is_file() or not is_text(path):
            continue
        name = rel(path)
        if name == SECRET_MANIFEST:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        extra = unknown_onions(text, allow)
        if extra:
            fails.append(name + ": new onion host (do not publish onions)")
        for kind in find_secrets(text):
            fails.append(name + ": " + kind)
        if name.startswith("public/"):
            claims = find_solve_claims(text)
            if claims:
                fails.append(name + ": solve-claim copy (school, not a break)")
    return fails


def self_check() -> list[str]:
    fails: list[str] = []
    allow = teaching_onions()
    if "gy3hoy2zizvuzvdb" not in allow:
        fails.append("published page-56 host missing from teaching allowlist")
    if len(allow) < 2:
        fails.append("ruled-out 8x16 host missing from teaching allowlist")
    fake_v2 = "a" * 16
    other_v2 = "b" * 16
    if fake_v2 not in find_onion_hosts("see " + fake_v2 + ".onion"):
        fails.append("v2 .onion detector miss")
    if unknown_onions("v2 onion                  gy3hoy2zizvuzvdb.onion", allow):
        fails.append("allowlisted published host flagged")
    if not unknown_onions("visit " + other_v2 + ".onion", allow):
        fails.append("unknown v2 host not flagged")
    pem = "-----" + "BEGIN RSA PRIVATE KEY" + "-----\nMII\n-----END RSA PRIVATE KEY-----"
    if not find_secrets(pem):
        fails.append("pem detector miss")
    if find_solve_claims("The preimage is still unsolved. This is a school."):
        fails.append("honest unsolved copy flagged as a claim")
    if not find_solve_claims("we solved liber primus yesterday"):
        fails.append("solve-claim detector miss")
    return fails


def main() -> int:
    allow = teaching_onions()
    fails = self_check()
    if fails:
        print("COOK GUARD SELF-CHECK FAIL " + "; ".join(fails), file=sys.stderr)
        return 1
    fails = scan_tree(allow)
    if fails:
        print("COOK GUARD FAIL", file=sys.stderr)
        for item in fails:
            print("  " + item, file=sys.stderr)
        return 1
    print("COOK GUARD OK")
    print("tracked tree has no secret manifest, no new onion, no credential shape,")
    print("and no Liber Primus solve claim in public copy.")
    print("This is not a decipherment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
