# INSTAR folder rules

- Canonical tree: this repo. Deploy `public/` with `deploy.ps1`.
- Product is a puzzle school. Do not paste plaintext answers into `public/`.
- `scripts/_secret_manifest.json` is local spoilers. Do not commit.
- EN only (i18n pause). ASCII dashes in public copy.
- After visual/copy change: OG `?v=` bump, Ensure-TweetCard, hits slug `instar`.
- Public GitHub: MIT, one commit, Pitchfork-and-Torch author, secret scan first.
- Before a page or lab PR: `python3 scripts/shed_check.py` (runs cook_guard, page56 lab, unit lab; no new locators, no secrets, no solve claims).
