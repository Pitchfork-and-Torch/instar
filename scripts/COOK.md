# INSTAR page-cook map

A school. Not a Cicada solve. Not a recruiter. ASCII only.

Do not paste plaintext answers into `public/`.
Do not commit `scripts/_secret_manifest.json`.
Do not publish onions. Do not add secrets. Do not claim a Liber Primus break.

The one command before a PR or deploy:

```
python3 scripts/shed_check.py
```

CI and `deploy.ps1` run the same gate. It does not open the secret journal. It is not a decipherment.

## When you change a thing

After visual or hello copy: bump `og.jpg?v=`, then `python3 scripts/ensure_tweet_card.py`. Hits slug stays `instar`: `python3 scripts/hits_check.py`. After `public/llms.txt`: `python3 scripts/llms_check.py`. Keep hello, the footer, and llms.txt saying this is not a Liber Primus solve.

After a new chamber: add it to `public/sw.js` `PRECACHE`, bump `CACHE`, keep `noindex`, then `python3 scripts/precache_check.py` and `python3 scripts/listing_check.py`.

After `public/_headers`: `python3 scripts/headers_check.py` and `python3 scripts/fresh_check.py`.

After `public/_redirects` or `public/404.html`: `python3 scripts/door_check.py`.

After `public/manifest.webmanifest` or install chrome on a public door: `python3 scripts/manifest_check.py`. After a seal or favicon edit: `python3 scripts/icon_check.py`.

After a new HTML page: keep `lang="en"`, no hreflang, then `python3 scripts/en_check.py`. EN only. i18n is paused. Also skip-to-content plus `main id="main"`: `python3 scripts/skip_check.py`.

After a new public door or a canonical edit: keep the href on-host, then `python3 scripts/canon_check.py`.

After a new `scripts/page*_lab.py`: local only, print `PAGE<n> OK`, no preimage hunt, no network client, then `python3 scripts/page_lab_contract.py`. The page 56 lab (`python3 scripts/page56_lab.py`) is the template.

Anytime: `python3 scripts/cook_guard.py` and `node scripts/unit_lab.js`.

Desk Playwright (`scripts/verify_lab.mjs`) is not in CI. Chromium first, Edge fallback. It covers skip+main on molt pages. Caesar NaN-key and LSB miss (green bit 3 vs red LSB) live in `unit_lab.js`.

## Deploy

```
powershell -ExecutionPolicy Bypass -File deploy.ps1
```

`deploy.ps1` runs `shed_check.py` first. A failed shed check does not deploy.
