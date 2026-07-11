"""
Indie Hackers has no official public API, so this scrapes their public group
pages instead. It's inherently more fragile than the Reddit/HN collectors
(official APIs) — if IH changes their page structure, this may need a fix.
It fails gracefully (returns []) rather than breaking the whole run.

No credentials needed.
"""
import re
import json
import time
import requests
from config import COMPLAINT_SIGNALS, LOOKBACK_DAYS

GROUPS = ["starting-up", "ideas", "growth", "indie-makers"]
BASE = "https://www.indiehackers.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (saas-radar research bot; contact via github)"}


def _matches_signal(text: str) -> bool:
    t = text.lower()
    return any(sig in t for sig in COMPLAINT_SIGNALS)


def _extract_next_data(html: str) -> dict | None:
    """IndieHackers is a Next.js app; page data is often embedded as JSON
    in a __NEXT_DATA__ script tag, which is far more reliable to parse
    than trying to match shifting CSS classes."""
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html, re.DOTALL,
    )
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def _posts_from_next_data(data: dict) -> list[dict]:
    """Best-effort walk through the Next.js data tree looking for anything
    that looks like a post (has a title/text-ish field). Structure may
    drift over time -- this is intentionally defensive."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            title = node.get("title") or node.get("headline")
            body = node.get("body") or node.get("text") or node.get("content") or ""
            slug = node.get("slug") or node.get("id")
            if title and isinstance(title, str):
                found.append({
                    "title": title,
                    "body": body if isinstance(body, str) else "",
                    "slug": slug,
                })
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return found


def collect_indiehackers_items() -> list[dict]:
    items = []

    for group in GROUPS:
        url = f"{BASE}/group/{group}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[indiehackers_collector] skipped group '{group}': {e}")
            continue

        data = _extract_next_data(resp.text)
        if data is None:
            print(f"[indiehackers_collector] no __NEXT_DATA__ found for '{group}' "
                  f"(site structure may have changed) — skipping")
            continue

        for post in _posts_from_next_data(data):
            combined = f"{post['title']}\n{post['body']}"
            if _matches_signal(combined):
                post_url = f"{BASE}/post/{post['slug']}" if post.get("slug") else url
                items.append({
                    "source": "indiehackers",
                    "subreddit": group,
                    "url": post_url,
                    "text": combined[:2000],
                    "created_utc": time.time(),  # IH doesn't expose this reliably via this method
                })

    return items
