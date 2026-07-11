"""
Pulls recent posts + top comments from target subreddits that look like
genuine complaints/pain points (matched against COMPLAINT_SIGNALS).

Needs env vars: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
(free to get at https://www.reddit.com/prefs/apps -> "create app" -> "script")
"""
import os
import time
import praw
from config import SUBREDDITS, COMPLAINT_SIGNALS, LOOKBACK_DAYS


def _matches_signal(text: str) -> bool:
    t = text.lower()
    return any(sig in t for sig in COMPLAINT_SIGNALS)


def collect_reddit_items() -> list[dict]:
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ.get("REDDIT_USER_AGENT", "saas-radar/1.0"),
    )
    reddit.read_only = True

    cutoff = time.time() - LOOKBACK_DAYS * 86400
    items = []

    for sub_name in SUBREDDITS:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.new(limit=75):
                if post.created_utc < cutoff:
                    continue

                combined_text = f"{post.title}\n{post.selftext or ''}"
                if _matches_signal(combined_text):
                    items.append({
                        "source": "reddit",
                        "subreddit": sub_name,
                        "url": f"https://reddit.com{post.permalink}",
                        "text": combined_text[:2000],
                        "created_utc": post.created_utc,
                    })

                # Also scan top-level comments for complaint language
                post.comments.replace_more(limit=0)
                for comment in post.comments[:15]:
                    body = getattr(comment, "body", "") or ""
                    if _matches_signal(body):
                        items.append({
                            "source": "reddit_comment",
                            "subreddit": sub_name,
                            "url": f"https://reddit.com{post.permalink}",
                            "text": body[:2000],
                            "created_utc": comment.created_utc,
                        })
        except Exception as e:
            print(f"[reddit_collector] skipped r/{sub_name}: {e}")
            continue

    return items
