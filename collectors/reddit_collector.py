"""
Pulls recent posts + top comments from target subreddits that look like
genuine complaints/pain points (matched against COMPLAINT_SIGNALS).

Uses Reddit's public read-only .json endpoints directly -- no OAuth app, no
credentials, no CAPTCHA. Self-service app registration at reddit.com/prefs/apps
started failing (CAPTCHA loop, "Responsible Builder Policy" gating) as of
mid-2026, so this avoids that path entirely. Anonymous access is rate-limited
by IP, so requests are throttled and this only fetches comments for posts that
already matched a signal (not every post), to stay well under any limit for a
once-a-day run.

No env vars needed.
"""
import time
import requests
from config import SUBREDDITS, COMPLAINT_SIGNALS, LOOKBACK_DAYS

HEADERS = {"User-Agent": "saas-radar/1.0 (research bot; public json endpoints, no auth)"}
REQUEST_DELAY_SECONDS = 1.5  # polite pacing to stay under anonymous rate limits


def _matches_signal(text: str) -> bool:
    t = text.lower()
    return any(sig in t for sig in COMPLAINT_SIGNALS)


def _get_json(url: str, params: dict | None = None) -> dict | None:
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[reddit_collector] request failed for {url}: {e}")
        return None
    finally:
        time.sleep(REQUEST_DELAY_SECONDS)


def _comments_for_post(sub_name: str, post_id: str) -> list[str]:
    data = _get_json(f"https://www.reddit.com/r/{sub_name}/comments/{post_id}.json", {"limit": 15})
    if not data or len(data) < 2:
        return []
    bodies = []
    for child in data[1].get("data", {}).get("children", [])[:15]:
        body = child.get("data", {}).get("body")
        if body:
            bodies.append(body)
    return bodies


def collect_reddit_items() -> list[dict]:
    cutoff = time.time() - LOOKBACK_DAYS * 86400
    items = []

    for sub_name in SUBREDDITS:
        data = _get_json(f"https://www.reddit.com/r/{sub_name}/new.json", {"limit": 75})
        if not data:
            continue

        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            created_utc = post.get("created_utc", 0)
            if created_utc < cutoff:
                continue

            post_id = post.get("id")
            permalink = post.get("permalink", "")
            combined_text = f"{post.get('title', '')}\n{post.get('selftext') or ''}"

            if _matches_signal(combined_text):
                items.append({
                    "source": "reddit",
                    "subreddit": sub_name,
                    "url": f"https://reddit.com{permalink}",
                    "text": combined_text[:2000],
                    "created_utc": created_utc,
                })

            # Only fetch comments for posts that already matched, or with
            # meaningful engagement -- keeps request volume low.
            if _matches_signal(combined_text) or post.get("num_comments", 0) >= 5:
                for body in _comments_for_post(sub_name, post_id):
                    if _matches_signal(body):
                        items.append({
                            "source": "reddit_comment",
                            "subreddit": sub_name,
                            "url": f"https://reddit.com{permalink}",
                            "text": body[:2000],
                            "created_utc": created_utc,
                        })

    return items
