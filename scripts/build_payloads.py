# Build INSTAR puzzle payloads. ASCII only. Run from repo root: py -3 scripts/build_payloads.py
from __future__ import annotations

import hashlib
import json
import math
import struct
import wave
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
MEDIA = PUB / "media"
STATIC = PUB / "static"
LIB = PUB / "library"
JS = PUB / "js"
MASTERS = ROOT / "assets" / "masters"


def sha_norm(s: str) -> str:
    n = "".join(ch for ch in s.lower() if ch.isalnum())
    return hashlib.sha256(n.encode("utf-8")).hexdigest()


def atbash(s: str) -> str:
    out = []
    for ch in s:
        if "A" <= ch <= "Z":
            out.append(chr(ord("Z") - (ord(ch) - ord("A"))))
        elif "a" <= ch <= "z":
            out.append(chr(ord("z") - (ord(ch) - ord("a"))))
        else:
            out.append(ch)
    return "".join(out)


def vigenere(plain: str, key: str) -> str:
    key = "".join(ch for ch in key.upper() if ch.isalpha())
    out = []
    ki = 0
    for ch in plain.upper():
        if not ch.isalpha():
            out.append(ch)
            continue
        k = ord(key[ki % len(key)]) - 65
        out.append(chr((ord(ch) - 65 + k) % 26 + 65))
        ki += 1
    return "".join(out)


def egcd(a: int, b: int):
    if a == 0:
        return b, 0, 1
    g, y, x = egcd(b % a, a)
    return g, x - (b // a) * y, y


def modinv(a: int, m: int) -> int:
    g, x, _ = egcd(a % m, m)
    if g != 1:
        raise ValueError("no inverse")
    return x % m


def write_clutch() -> None:
    msg = "THE FIRST GATE IS NYMPHED"
    body = atbash(msg)
    text = (
        body
        + "\n\n"
        + "tools rust in the open\n"
        + "/workbench/\n"
    )
    (STATIC / "clutch.txt").write_text(text, encoding="utf-8")


def write_journal() -> dict:
    # Atmospheric original journal. Target words planted at known line:word (1-based).
    lines = [
        "Winter counts in silence under the orchard row.",
        "The nymph drinks minerals and does not dream.",
        "Seventeen lids of frost press the dark.",
        "A mouth in the soil is not a grave. It is a workshop.",
        "Veins remember rivers the eye has not met.",
        "Wait is a craft. Hurry is a leak.",
        "Do not EXTRACT color until the black has spoken.",
        "Ink sits on a page. Meaning sits under a page.",
        "The first 3301 thread hid a book inside a book.",
        "Coordinates are kindness if you already hold the volume.",
        "LEAST of all should you trust the brightest bit.",
        "A picture is a trench. Dig the last row.",
        "OutGuess was a tool. Least significant bits are a habit.",
        "If a file is heavier than its face, ask why.",
        "Cicadas do not shout. They leave a husk and a frequency.",
        "A spectrogram is a letter written in heat.",
        "Prime years are not poetry. They are a lock.",
        "Count the BITS that nobody painted on purpose.",
        "When the wing is spent, the song begins.",
        "We do not want a name. We want you to notice.",
    ]
    targets = {"EXTRACT": None, "LEAST": None, "BITS": None}
    indexed = []
    for li, line in enumerate(lines, start=1):
        words = line.split()
        for wi, w in enumerate(words, start=1):
            bare = "".join(ch for ch in w if ch.isalpha()).upper()
            if bare in targets and targets[bare] is None:
                targets[bare] = f"{li}:{wi}"
            indexed.append((li, wi, bare, w))
    missing = [k for k, v in targets.items() if v is None]
    if missing:
        raise SystemExit(f"journal missing planted words: {missing}")
    LIB.mkdir(parents=True, exist_ok=True)
    (LIB / "soil-journal.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "coords": [targets["EXTRACT"], targets["LEAST"], targets["BITS"]],
        "plain": "EXTRACT LEAST BITS",
    }


def encode_lsb_png() -> None:
    src = MASTERS / "wing-macro.jpg"
    img = Image.open(src).convert("RGB")
    # Mild flatten so LSB noise is invisible
    img = ImageEnhance.Contrast(img).enhance(1.02)
    payload = (
        "the song is a picture\n"
        "/song/\n"
        "\n"
        "unused door: /brood/\n"
    ).encode("utf-8")
    bits = []
    for byte in payload + b"\x00":
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    pixels = list(img.getdata())
    if len(bits) > len(pixels):
        raise SystemExit("payload larger than image")
    out_px = []
    for i, (r, g, b) in enumerate(pixels):
        if i < len(bits):
            r = (r & 0xFE) | bits[i]
        out_px.append((r, g, b))
    img.putdata(out_px)
    png_path = MEDIA / "wing.png"
    img.save(png_path, format="PNG", optimize=True)
    # Append a readable tail after IEND so a strings pass finds a second door.
    tail = b"\nINSTAR-TAIL:the unused door is /brood/\n"
    data = png_path.read_bytes() + tail
    png_path.write_bytes(data)


def write_spectrogram_wav() -> None:
    # Paint "3301 IS PRIME" into a spectrogram via column sines.
    text = "3301 IS PRIME"
    w, h = 900, 256
    canvas = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(str(ROOT / "public/fonts/fontshare/clash-display/otf/ClashDisplay-Bold.otf"), 54)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) / 2, (h - th) / 2 - 8), text, fill=255, font=font)
    canvas = canvas.filter(ImageFilter.GaussianBlur(0.6))

    sr = 44100
    duration = 7.0
    n = int(sr * duration)
    samples = [0.0] * n
    cols = w
    rows = h
    f_lo, f_hi = 420.0, 3400.0
    for x in range(cols):
        t0 = int((x / cols) * n)
        t1 = int(((x + 1) / cols) * n)
        if t1 <= t0:
            continue
        for y in range(rows):
            lum = canvas.getpixel((x, y))
            if lum < 40:
                continue
            # image y=0 is top = high frequency
            frac = 1.0 - (y / (rows - 1))
            freq = f_lo + frac * (f_hi - f_lo)
            amp = (lum / 255.0) * 0.045
            for t in range(t0, t1):
                samples[t] += amp * math.sin(2.0 * math.pi * freq * (t / sr))
    # Add faint soil noise so it is not a pure beep
    seed = 3301
    for t in range(n):
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        noise = ((seed / 0x7FFFFFFF) - 0.5) * 0.012
        samples[t] += noise
        # soft edges
        env = 1.0
        fade = int(0.08 * sr)
        if t < fade:
            env = t / fade
        elif t > n - fade:
            env = (n - t) / fade
        samples[t] *= env
    peak = max(1e-9, max(abs(s) for s in samples))
    frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s / peak * 0.85)) * 32767)) for s in samples)
    MEDIA.mkdir(parents=True, exist_ok=True)
    with wave.open(str(MEDIA / "emergence.wav"), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(frames)


def rsa_block() -> dict:
    p, q = 43, 73
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 17
    d = modinv(e, phi)
    word = "LIBER"
    letters = []
    for ch in word:
        m = ord(ch)
        c = pow(m, e, n)
        letters.append({"ch": ch, "m": m, "c": c})
    return {
        "p": p,
        "q": q,
        "n": n,
        "e": e,
        "d": d,
        "phi": phi,
        "word": word,
        "cipher": [x["c"] for x in letters],
        "letters": letters,
    }


def write_hashes(journal: dict, rsa: dict) -> dict:
    answers = {
        "nymph": "periodical",
        "soil": "extractleastbits",
        "song": "3301isprime",
        "prime": "liber",
        "liber": "emerge",
        "final": "theperiodicalemerges",
    }
    hashes = {k: sha_norm(v) for k, v in answers.items()}
    JS.mkdir(parents=True, exist_ok=True)
    payload = {
        "v": "1.1.2",
        "hashes": hashes,
        "vigenereCipher": vigenere("PERIODICAL", "TIBERIVSCLAVDIVSCAESAR"),
        "vigenereHint": "TIBERIVS CLAVDIVS CAESAR",
        "bookCoords": journal["coords"],
        "rsa": {"n": rsa["n"], "e": rsa["e"], "c": rsa["cipher"]},
    }
    (JS / "puzzle.js").write_text(
        "window.INSTAR_PUZZLE = " + json.dumps(payload, indent=2) + ";\n",
        encoding="utf-8",
    )
    secret = {
        "answers": answers,
        "atbash": atbash("THE FIRST GATE IS NYMPHED"),
        "rsa": rsa,
        "journal": journal,
        "hashes": hashes,
    }
    (ROOT / "scripts" / "_secret_manifest.json").write_text(
        json.dumps(secret, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def font_path(name: str) -> Path | None:
    cands = [
        ROOT / "public/fonts/fontshare/clash-display/otf" / name,
        ROOT / "public/fonts/fontshare/satoshi/otf" / name,
    ]
    for c in cands:
        if c.exists():
            return c
    return None


def make_og() -> None:
    W, H = 1200, 630
    hero = Image.open(MASTERS / "hero-soil-wing.jpg").convert("RGB")
    # cover-crop
    scale = max(W / hero.width, H / hero.height)
    hero = hero.resize((int(hero.width * scale), int(hero.height * scale)), Image.Resampling.LANCZOS)
    left = (hero.width - W) // 2
    top = (hero.height - H) // 2 + 20
    card = hero.crop((left, top, left + W, top + H))
    # darken lower third for type
    overlay = Image.new("RGB", (W, H), (8, 7, 5))
    card = Image.blend(card, overlay, 0.28)
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        a = 0
        if y > 280:
            a = int(200 * ((y - 280) / 350))
        sd.line([(0, y), (W, y)], fill=min(220, a))
    black = Image.new("RGB", (W, H), (8, 7, 5))
    card = Image.composite(black, card, shade)
    draw = ImageDraw.Draw(card)
    display = font_path("ClashDisplay-Semibold.otf") or font_path("ClashDisplay-Bold.otf")
    sans = font_path("Satoshi-Medium.otf") or font_path("Satoshi-Regular.otf")
    f_kicker = ImageFont.truetype(str(sans), 22) if sans else ImageFont.load_default()
    f_title = ImageFont.truetype(str(display), 92) if display else ImageFont.load_default()
    f_sub = ImageFont.truetype(str(sans), 28) if sans else ImageFont.load_default()
    ink = (232, 220, 200)
    mute = (196, 163, 106)
    draw.text((72, 390), "A SCHOOL FOR CICADA 3301 TRADECRAFT", font=f_kicker, fill=mute)
    draw.text((68, 424), "INSTAR", font=f_title, fill=ink)
    draw.text((72, 540), "Seven molts. One emergence.", font=f_sub, fill=(180, 168, 150))
    jpg = PUB / "og.jpg"
    png = PUB / "og.png"
    card.save(jpg, "JPEG", quality=90, optimize=True)
    card.save(png, "PNG", optimize=True)
    card.resize((1280, 672), Image.Resampling.LANCZOS).crop((0, 0, 1280, 720)).save(
        ROOT / "assets" / "masters" / "hive-instar-1280x720.jpg", "JPEG", quality=88
    )


def main() -> None:
    MEDIA.mkdir(parents=True, exist_ok=True)
    STATIC.mkdir(parents=True, exist_ok=True)
    write_clutch()
    journal = write_journal()
    encode_lsb_png()
    write_spectrogram_wav()
    rsa = rsa_block()
    payload = write_hashes(journal, rsa)
    make_og()
    print("clutch", (STATIC / "clutch.txt").read_text(encoding="utf-8").splitlines()[0])
    print("vigenere", payload["vigenereCipher"])
    print("coords", journal["coords"])
    print("rsa", rsa["n"], rsa["e"], rsa["cipher"], "d", rsa["d"])
    print("wav", (MEDIA / "emergence.wav").stat().st_size)
    print("wing", (MEDIA / "wing.png").stat().st_size)
    print("og", (PUB / "og.jpg").stat().st_size)
    print("ok")


if __name__ == "__main__":
    main()
