# INSTAR folder rules

- Canonical tree: this repo. Deploy `public/` with `deploy.ps1` (runs shed_check first; no secrets).
- Product is a puzzle school. Do not paste plaintext answers into `public/`.
- `scripts/_secret_manifest.json` is local spoilers. Do not commit.
- EN only (i18n pause). ASCII dashes in public copy.
- After visual/copy change: OG `?v=` bump, `python3 scripts/ensure_tweet_card.py`, hits slug `instar`.
- Public GitHub: MIT, one commit, Pitchfork-and-Torch author, secret scan first.
- Before a page or lab PR: `python3 scripts/shed_check.py` (runs cook_guard, page56 lab, unit lab, Ensure-TweetCard, precache, headers, listing; no new locators, no secrets, no solve claims).
- After a new chamber: add it to `public/sw.js` `PRECACHE`, bump `CACHE`, keep it `noindex`, run `python3 scripts/precache_check.py` and `python3 scripts/listing_check.py`.
