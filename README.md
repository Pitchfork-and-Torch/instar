# INSTAR

A school for the cryptography [Cicada 3301](https://en.wikipedia.org/wiki/Cicada_3301) actually used.

Original seven-molt puzzle. Not affiliated. Not a recruiter. No identity collection.

Live: https://instar.jonbailey.xyz/

## What you practice

- View-source and hidden static files
- Atbash, then Vigenere (the 2012 emperor-key move, new plaintext)
- Book cipher against a local journal
- LSB steganography and a strings tail
- Audio spectrograms
- Classroom RSA (factor, invert, decrypt)
- Futhorc sound values (not Liber Primus gematria)
- A signed-statement / onion primer in the field manual
- Page 56 as a payload reading (ruled-out paths, no preimage search)

## Play

Open the live site. Begin at Hello. The first molt is not on the page you see.

Workbench (always open): `/workbench/`

v1.1 keeps the same hashed gates. The workbench is a living lab (live dual pane, frequency, bit-planes, STFT sliders, RSA steps). Depth marks molt without scores. Optional Guide names the next neighborhood, never the lock. Optional Skins shows shed depth as dots only, off by default, names stay unspoken. Optional Soil is a low tone, off by default. The school installs as a quiet PWA.

## Local

```
npx --yes serve public
```

Rebuild puzzle payloads (spoilers live in the encoder):

```
py -3 scripts/build_payloads.py
```

Page 56 lab (public hex, no preimage search):

```
python3 scripts/page56_lab.py
```

Field lesson: `/husk/`

Page cook guard (no spoilers, no decipherment):

```
python3 scripts/cook_guard.py
```

The guard fails if a cook is about to commit the secret manifest, a new onion host, a credential shape, or a Liber Primus solve claim. The published dead page-56 v2 host stays allowlisted as a teaching artifact. Do not add a live hidden service. Do not claim a Cicada break.

Shed check (public-safe school gate, no secret journal). Run before a chamber or lab PR. CI runs the same command:

```
python3 scripts/shed_check.py
```

The shed check runs the cook guard, the page 56 lab, the unit lab, and Ensure-TweetCard, then confirms the browser and CLI labs still agree, required public files are present, no new magnet / IPFS / Freenet / I2P locator landed, public copy stayed ASCII, the hello tweet card and hits slug `instar` still hold, and README / AGENTS.md do not claim a break. It does not open `scripts/_secret_manifest.json`. It is not a decipherment.

Ensure-TweetCard (after a visual or copy change; does not bump `?v=`):

```
python3 scripts/ensure_tweet_card.py
```

The card check fails if `public/og.jpg` is missing, `og:image` / `twitter:image` / JSON-LD disagree on `?v=`, `llms.txt` Version drifted, or the hello hits slug is not `instar`. Cooks still bump `?v=` on purpose when the picture or hello copy changes.

## Deploy

```
powershell -ExecutionPolicy Bypass -File deploy.ps1
```

Cloudflare Pages project `instar-jonbailey`. Custom host `instar.jonbailey.xyz`.

## License

MIT. See `LICENSE`.
