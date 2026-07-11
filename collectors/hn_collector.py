"""
Pulls recent Hacker News stories/comments matching our search queries.
Uses the free, keyless Algolia HN Search API — no API key required.
"""
import time
import requests
from config import HN_QUERIES, LOOKBACK_DAYS

HN_API = "https://hn.algolia.com/api/v1/search_by_date"


def collect_hn_items() -> list[dict]:
    cutoff_ts = int(time.time() - LOOKBACK_DAYS * 86400)
    items = []

    for query in HN_QUERIES:
        try:
            resp = requests.get(
                HN_API,
                params={
                    "query": query,
                    "tags": "(story,comment)",
                    "numericFilters": f"created_at_i>{cutoff_ts}",
                    "hitsPerPage": 30,
                },
                timeout=15,
            )
            resp.raise_for_status()
            hits = resp.json().get("hits", [])

            for hit in hits:
                text = hit.get("story_text") or hit.get("comment_text") or hit.get("title") or ""
                if not text.strip():
                    continue
                object_id = hit.get("objectID")
                items.append({
                    "source": "hackernews",
                    "subreddit": None,
                    "url": f"https://news.ycombinator.com/item?id={object_id}",
                    "text": text[:2000],
                    "created_utc": hit.get("created_at_i", time.time()),
                })
        except Exception as e:
            print(f"[hn_collector] skipped query '{query}': {e}")
            continue

    return items
