# SaaS Opportunity Radar

Scans Reddit, Hacker News, Indie Hackers, and (optionally) Product Hunt daily
for people complaining about problems worth turning into a SaaS, scores each
one, and emails you a ranked digest every morning. Runs itself forever for
free via GitHub Actions — no server needed.

## One-time setup (~10 minutes total)

### 1. Put this in a GitHub repo
- Create a new repo on github.com (private is fine)
- Upload all these files into it (or `git init` + push from this folder)

### 2. Get 3 sets of free credentials

| What | Where | Time |
|---|---|---|
| Anthropic API key | console.anthropic.com → Get API Key | 1 min |
| Gmail app password | myaccount.google.com/apppasswords (needs 2FA on) | 2 min |
| — | (your own email address to receive the digest) | — |

No Reddit API credentials needed — the Reddit collector uses Reddit's public
read-only `.json` endpoints directly, since self-service OAuth app registration
at reddit.com/prefs/apps started failing (CAPTCHA loop, gated behind a
"Responsible Builder Policy" review) as of mid-2026.

### 3. Add them as GitHub repo secrets
Repo → Settings → Secrets and variables → Actions → New repository secret.
Add all of these:
- `ANTHROPIC_API_KEY`
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
- Anthropic API: a few cents/day depending on volume (Claude does the reading
  + scoring, plus a light web search per batch to sanity-check competition)

## Known limitations (by design, to keep this reliable and free)
- G2/Capterra/Trustpilot reviews aren't scraped — those sites actively block
  automated scraping, and a fragile scraper would break constantly and risk
  getting your IP blocked. If you want that data, checking a handful of review
  pages manually once a week for your top few flagged ideas is the safer move.
- Twitter/X isn't included — their API pricing makes this not worth it for
  a bootstrapped setup.
- Indie Hackers has no official API, so that collector scrapes their public
  group pages directly. It's built defensively (fails silently, logs a
  warning) but is inherently less reliable than the HN collector — if IH
  changes their site structure, check the Action logs for
  "[indiehackers_collector]" warnings and let me know so it can be patched.
- The Reddit collector uses public `.json` endpoints (no OAuth app) since
  self-service registration is currently broken (CAPTCHA loop that never
  resolves). Confirmed from one network, these anonymous endpoints return a
  flat 403 (Reddit's bot-detection layer, not just a rate limit) — they may or
  may not fare differently from GitHub Actions' IP ranges; that's untested
  either way. It fails safely regardless: zero Reddit items that day, logged
  as a "[reddit_collector]" warning, rest of the run continues normally. This
  is exactly why Product Hunt was added as a second, more reliable source —
  if Reddit stays dead, HN + Indie Hackers + Product Hunt still carry the
  digest. If Reddit fixes app registration later, switch back to an
  authenticated OAuth-based collector for better reliability.
