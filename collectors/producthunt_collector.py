"""
Pulls recent Product Hunt launches + top comments. Launch taglines/descriptions
and comments often contain "I built this because X was broken" / "does this
handle Y" pain-point language -- a different angle than Reddit/HN (signals
what people are already trying to solve, and what commenters say is missing).

Optional: needs env var PRODUCTHUNT_TOKEN (a Developer Token, not full OAuth --
create an app at https://api.producthunt.com/v2/oauth/applications, then
generate a token directly from the app page, no approval wait). If unset, this
collector is skipped entirely (main.py treats it the same as zero results).
"""
import os
import time
import requests
from config import COMPLAINT_SIGNALS, LOOKBACK_DAYS

API_URL = "https://api.producthunt.com/v2/api/graphql"

QUERY = """
query RecentPosts($after: DateTime!) {
  posts(order: NEWEST, postedAfter: $after, first: 30) {
    edges {
      node {
        id
        name
        tagline
        description
        url
        createdAt
        comments(first: 10) {
          edges { node { body } }
        }
      }
    }
  }
}
"""


def _matches_signal(text: str) -> bool:
    t = text.lower()
    return any(sig in t for sig in COMPLAINT_SIGNALS)


def collect_producthunt_items() -> list[dict]:
    token = os.environ.get("PRODUCTHUNT_TOKEN")
    if not token:
        print("[producthunt_collector] PRODUCTHUNT_TOKEN not set, skipping (optional source)")
        return []

    cutoff_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - LOOKBACK_DAYS * 86400))

    try:
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"query": QUERY, "variables": {"after": cutoff_iso}},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[producthunt_collector] request failed: {e}")
        return []

    if "errors" in data:
        print(f"[producthunt_collector] API returned errors: {data['errors']}")
        return []

    items = []
    for edge in data.get("data", {}).get("posts", {}).get("edges", []):
        post = edge["node"]
        combined_text = f"{post.get('tagline', '')}\n{post.get('description') or ''}"

        if _matches_signal(combined_text):
            items.append({
                "source": "producthunt",
                "subreddit": None,
                "url": post.get("url"),
                "text": combined_text[:2000],
                "created_utc": time.time(),
            })

        for c_edge in post.get("comments", {}).get("edges", []):
            body = c_edge.get("node", {}).get("body", "") or ""
            if _matches_signal(body):
                items.append({
                    "source": "producthunt_comment",
                    "subreddit": None,
                    "url": post.get("url"),
                    "text": body[:2000],
                    "created_utc": time.time(),
                })

    return items
