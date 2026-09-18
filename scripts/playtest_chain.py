# Offline verification of the INSTAR chain. No spoilers printed unless --show.
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
secret = json.loads((ROOT / "scripts" / "_secret_manifest.json").read_text(encoding="utf-8"))


def sha_norm(s: str) -> str:
    n = "".join(ch for ch in s.lower() if ch.isalnum())
    return hashlib.sha256(n.encode("utf-8")).hexdigest()


def atbash(s: str) -> str:
    out = []
    for ch in s:
        if "A" <= ch <= "Z":
            out.append(chr(ord("Z") - (ord(ch) - ord("A"))))
        else:
            out.append(ch)
    return "".join(out)


def fail(msg: str) -> None:
    print("FAIL", msg)
    sys.exit(1)


def main() -> None:
    clutch = (PUB / "static" / "clutch.txt").read_text(encoding="utf-8")
    first = clutch.splitlines()[0]
    if atbash(first) != "THE FIRST GATE IS NYMPHED":
        fail("clutch atbash")

    journal = (PUB / "library" / "soil-journal.txt").read_text(encoding="utf-8").splitlines()
    words = []
    for tok in secret["journal"]["coords"]:
        li, wi = [int(x) for x in tok.split(":")]
        words.append("".join(ch for ch in journal[li - 1].split()[wi - 1] if ch.isalpha()))
    if " ".join(w.upper() for w in words) != "EXTRACT LEAST BITS":
        fail("book " + str(words))

    img = Image.open(PUB / "media" / "wing.png").convert("RGB")
    bits = [(r & 1) for r, g, b in img.getdata()]
    raw = bytearray()
    for i in range(0, len(bits) - 7, 8):
        v = 0
        for j in range(8):
            v = (v << 1) | bits[i + j]
        if v == 0:
            break
        raw.append(v)
    text = raw.decode("utf-8")
    if "/song/" not in text or "/brood/" not in text:
        fail("lsb " + text[:80])
    tail = (PUB / "media" / "wing.png").read_bytes()
    if b"INSTAR-TAIL" not in tail:
        fail("png tail")

    wav = (PUB / "media" / "emergence.wav").read_bytes()
    if len(wav) < 10000:
        fail("wav tiny")

    rsa = secret["rsa"]
    word = "".join(chr(pow(c, rsa["d"], rsa["n"])) for c in rsa["cipher"])
    if word != "LIBER":
        fail("rsa " + word)

    for name, ans in secret["answers"].items():
        if sha_norm(ans) != secret["hashes"][name]:
            fail("hash " + name)

    for p in [
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
        "og.jpg",
        "llms.txt",
    ]:
        if not (PUB / p).exists():
            fail("missing " + p)

    lab = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "page56_lab.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if lab.returncode != 0 or "PAGE56 OK" not in lab.stdout:
        fail("page56 lab")
    if "gy3hoy2zizvuzvdb" not in lab.stdout:
        fail("page56 onion")
    if "SHA3-512" not in lab.stdout:
        fail("page56 sha3 note")

    print("PLAYTEST OK")
    if "--show" in sys.argv:
        print(json.dumps(secret["answers"], indent=2))


if __name__ == "__main__":
    main()
