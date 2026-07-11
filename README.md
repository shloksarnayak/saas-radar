# SaaS Opportunity Radar

Scans Reddit, Hacker News, Indie Hackers, and (optionally) Product Hunt daily
for people complaining about problems worth turning into a SaaS, scores each
one, and emails you a ranked digest every morning. Runs itself forever for
free via GitHub Actions — no server needed.

## One-time setup (~10 minutes total)

### 1. Put this in a GitHub repo
- Create a new repo on github.com (private is fine)
- Upload all these files into it (or `git init` + push from this folder)

### 2. Get 3 sets of credentials

| What | Where | Time |
|---|---|---|
| Gemini API key | aistudio.google.com/apikey → Create API Key (needs billing enabled for paid-tier volume) | 1 min |
| Gmail app password | myaccount.google.com/apppasswords (needs 2FA on) | 2 min |
| — | (your own email address to receive the digest) | — |

Using Gemini rather than Claude for the scoring step specifically because
Anthropic's console billing only accepts Visa/Mastercard with international
transactions enabled — no UPI, which rules it out for a lot of Indian
accounts. Gemini's billing supports Indian payment methods directly.

No Reddit API credentials needed — the Reddit collector uses Reddit's public
read-only `.json` endpoints directly, since self-service OAuth app registration
at reddit.com/prefs/apps started failing (CAPTCHA loop, gated behind a
"Responsible Builder Policy" review) as of mid-2026.

### 3. Add them as GitHub repo secrets
Repo → Settings → Secrets and variables → Actions → New repository secret.
Add all of these:
- `GEMINI_API_KEY`
- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD`
- `DIGEST_TO_ADDRESS` (the email you want the digest sent to)
- `PRODUCTHUNT_TOKEN` — optional. api.producthunt.com/v2/oauth/applications →
  create app → generate a "Developer Token" directly on the app page (no
  approval wait). Skip this one entirely and everything else still works.

### 4. Done
The workflow runs automatically every day at 07:00 UTC. You can also trigger
it immediately: repo → Actions tab → "Daily SaaS Opportunity Scan" → Run workflow.

## Tuning it later (no code needed)
Everything you'd want to adjust lives in `config.py`:
- `SUBREDDITS` — add/remove communities to scan
- `COMPLAINT_SIGNALS` — phrases that flag a post as a real complaint
- `MIN_SCORE_TO_REPORT` — raise this if the digest is too noisy, lower it if too quiet

## What it costs
- GitHub Actions: free (well under the free-tier minutes for a daily job)
- Reddit: free (public read-only endpoints, no key)
- Hacker News API: free
- Gemini API: a few cents/day depending on volume (Gemini does the reading
  + scoring, plus Google Search grounding per batch to sanity-check competition)

## Known limitations (by design, to keep this reliable and free)
- G2/Capterra/Trustpilot reviews aren't scraped — those sites actively block
  automated scraping, and a fragile scraper would break constantly and risk
  getting your IP blocked. If you want that data, checking a handful of review
  pages manually once a week for your top few flagged ideas is the safer move.
- Twitter/X isn't included — their API pricing makes this not worth it for
  a bootstrapped setup.
- **Indie Hackers currently returns zero items.** Confirmed: IH migrated off
  the Next.js `__NEXT_DATA__` pattern this collector was written for — the
  site now renders entirely client-side via Firebase (Firestore/Realtime DB)
  + Algolia, so there's no server-embedded data in the raw HTML to parse at
  all. Fixing this properly needs either a headless browser to execute their
  JS, or reverse-engineering their Firebase project config out of minified
  bundles to hit Firestore's REST API directly — deliberately not done yet,
  since it's disproportionate effort for one of four sources. It fails
  safely (zero items, logged warning, rest of the run continues).
- **The Reddit collector uses public `.json` endpoints (no OAuth app) and is
  confirmed blocked, including from GitHub Actions' own IP ranges** — flat
  403s (Reddit's bot-detection layer, not a rate limit) on every subreddit,
  tested directly. It fails safely (zero Reddit items, logged warning) rather
  than crashing the run. This is exactly why Product Hunt was added as a
  second, more reliable source, and why HN carries most of the current
  signal. If Reddit fixes self-service app registration later, switch back to
  an authenticated OAuth-based collector for better reliability.
