# Page 56 lab. Public hex only. ASCII. No preimage search.
# Run from repo root: python3 scripts/page56_lab.py
from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

HEX = (
    "36367763ab73783c7af284446c59466b4cd653239a311cb7116d4618dee09a84"
    "25893dc7500b464fdaf1672d7bef5e891c6e2274568926a49fb4f45132c2a8b4"
)
# Published Liber Primus lineation (five uneven lines, 128 hex chars).
LINES = [
    "36367763ab73783c7af284446c",
    "59466b4cd653239a311cb7116",
    "d4618dee09a8425893dc7500b",
    "464fdaf1672d7bef5e891c6e227",
    "4568926a49fb4f45132c2a8b4",
]
ONION_V2 = "gy3hoy2zizvuzvdb"
SHA3_FIPS_202 = "2015-08-05"
LIBER_PRIMUS_YEAR = 2014


def first8(lines: list[str]) -> str:
    return "".join(ln[:8] for ln in lines)


def after8(lines: list[str]) -> str:
    return "".join(ln[8:] for ln in lines)


def chunks(hex_s: str, n: int) -> list[str]:
    return [hex_s[i : i + n] for i in range(0, len(hex_s), n)]


def onion_from_extract(hex40: str) -> str:
    raw = bytes.fromhex(hex40)
    return base64.b32encode(raw[:10]).decode("ascii").lower().rstrip("=")


def magnet_btih(hex40: str) -> str:
    return "magnet:?xt=urn:btih:" + hex40


def try_gcm(path: Path, key: bytes, nonce: bytes) -> str:
    data = path.read_bytes()
    if len(data) < 16:
        return "too short for a GCM tag (need ciphertext plus a 16-byte tag)"
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    except ImportError:
        return (
            "cryptography not installed; layout is printed above. "
            "Any AES-256-GCM opener will do. Do not invent a blob."
        )
    try:
        AESGCM(key).decrypt(nonce, data, None)
    except Exception:
        return "auth fail (expected until a real published blob appears)"
    return "AUTH OK (unexpected). Report the method. Do not paste a guessed preimage."


def self_check() -> list[str]:
    fails: list[str] = []
    raw = bytes.fromhex(HEX)
    if len(raw) != 64:
        fails.append("digest is not 64 bytes")
    if "".join(LINES) != HEX:
        fails.append("five-line wrap does not rejoin the digest")
    if sum(len(ln) for ln in LINES) != 128:
        fails.append("line lengths do not sum to 128 hex chars")
    extract = first8(LINES)
    leftover = after8(LINES)
    if len(extract) != 40:
        fails.append("extract is not 160 bits")
    if len(leftover) != 88:
        fails.append("leftover is not 352 bits")
    if onion_from_extract(extract) != ONION_V2:
        fails.append("published extract does not yield the v2 onion")
    if onion_from_extract(first8(chunks(HEX, 16))) == ONION_V2:
        fails.append("8x16 wrap should not yield the onion")
    wrap4 = first8(chunks(HEX, 32))
    if len(wrap4) != 32:
        fails.append("4x32 wrap is not 128 bits")
    if onion_from_extract(wrap4) == ONION_V2:
        fails.append("4x32 wrap should not yield the onion")
    if raw[37] != 0x0B:
        fails.append("byte 37 is not 0x0B")
    if SHA3_FIPS_202 < "2015":
        fails.append("SHA-3 date constant drifted")
    if LIBER_PRIMUS_YEAR >= 2015:
        fails.append("Liber Primus year constant drifted")
    return fails


def report() -> str:
    extract = first8(LINES)
    leftover = after8(LINES)
    lines = [
        "INSTAR page 56 lab",
        "A 512-bit dump can be a payload. This is not a preimage search.",
        "",
        "digest  " + HEX,
        "bytes   64",
        "lines   " + ",".join(str(len(ln)) for ln in LINES) + " hex chars (published wrap)",
        "",
        "extract first-8-per-line  " + extract,
        "extract bits              160",
        "v2 onion                  " + ONION_V2 + ".onion",
        "v2 status                 dead since Tor removed v2 (2021-10)",
        "do not visit              a dead address is not a living door",
        "",
        "leftover bits             352",
        "AES-256-GCM shape         key 256 || nonce 96 (unverified; no ciphertext on the page)",
        "key                       " + leftover[:64],
        "nonce                     " + leftover[64:],
        "",
        "ruled out",
        "- SHA-512 / BLAKE-512 / Whirlpool preimage: 512-bit invert is not the work",
        "- CP1252 paste: same 64 bytes; byte 37 is 0x0B (VT) and becomes a blank line",
        "- SHA3-512: FIPS 202 is " + SHA3_FIPS_202 + "; Liber Primus is " + str(LIBER_PRIMUS_YEAR),
        "- 8x16 wrap first-8: " + first8(chunks(HEX, 16)),
        "  onion " + onion_from_extract(first8(chunks(HEX, 16))) + " (not the published host)",
        "- 4x32 wrap first-8: " + first8(chunks(HEX, 32)) + " (128 bits; not an onion)",
        "- magnet template: " + magnet_btih(extract),
        "  BitTorrent infohash width matches 160 bits. No known swarm.",
        "- IPFS CIDv0 wants SHA-256 (256 bits). This dump is 512 bits and not SHA-256.",
        "- Freenet CHK is not a raw hex dump. I2P b32 dest is SHA-256, 52 chars.",
        "  Locator templates have been formatted. None resolve to known content.",
        "",
        "bounded next experiment",
        "If you already hold a published candidate blob (another public hex dump,",
        "an archived 2014 payload), offer it as ciphertext+tag:",
        "  python3 scripts/page56_lab.py --gcm path/to/blob",
        "Auth-fail is the expected result. Do not invent a blob.",
        "Do not fetch live hidden services. Do not GPU-thrash a 512-bit digest.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="INSTAR page 56 lab. No preimage search.")
    parser.add_argument(
        "--gcm",
        metavar="FILE",
        help="optional local ciphertext+tag to try as AES-256-GCM with leftover key||nonce",
    )
    args = parser.parse_args()

    fails = self_check()
    if fails:
        print("PAGE56 FAIL " + ", ".join(fails), file=sys.stderr)
        return 1

    sys.stdout.write(report())

    if args.gcm:
        leftover = bytes.fromhex(after8(LINES))
        key, nonce = leftover[:32], leftover[32:]
        path = Path(args.gcm)
        if not path.is_file():
            print("gcm file missing: " + str(path), file=sys.stderr)
            return 1
        print("gcm key||nonce  " + try_gcm(path, key, nonce))
        print("gcm nonce||key  " + try_gcm(path, leftover[12:], leftover[:12]))

    print("PAGE56 OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
