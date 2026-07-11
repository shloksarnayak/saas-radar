"""
Entry point. Run this daily (GitHub Actions handles the schedule automatically).

    python main.py
"""
from collectors.reddit_collector import collect_reddit_items
from collectors.hn_collector import collect_hn_items
from collectors.indiehackers_collector import collect_indiehackers_items
from scorer import score_items
from storage import update_and_filter
from notifier import send_digest


def main():
    print("[main] collecting from Reddit...")
    reddit_items = collect_reddit_items()
    print(f"[main] got {len(reddit_items)} candidate items from Reddit")

    print("[main] collecting from Hacker News...")
    hn_items = collect_hn_items()
    print(f"[main] got {len(hn_items)} candidate items from Hacker News")

    print("[main] collecting from Indie Hackers...")
    ih_items = collect_indiehackers_items()
    print(f"[main] got {len(ih_items)} candidate items from Indie Hackers")

    all_items = reddit_items + hn_items + ih_items
    print(f"[main] scoring {len(all_items)} total items with Claude...")
    scored = score_items(all_items)
    print(f"[main] {len(scored)} items cleared the score bar")

    to_report = update_and_filter(scored)
    print(f"[main] {len(to_report)} items are new/trending -> sending digest")

    send_digest(to_report)


if __name__ == "__main__":
    main()
