"""
Tiny JSON-file "database" that persists between runs because GitHub Actions
commits data/seen.json back into the repo after every run (see the workflow).

Tracks each distinct opportunity (by a normalized theme key) so the digest
only surfaces things that are NEW or actively TRENDING UP, instead of
repeating the same flagged idea every single day.
"""
import json
import os
from datetime import datetime, timezone

STORE_PATH = os.path.join(os.path.dirname(__file__), "data", "seen.json")


def load_store() -> dict:
    if not os.path.exists(STORE_PATH):
        return {}
    with open(STORE_PATH, "r") as f:
        return json.load(f)


def save_store(store: dict) -> None:
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w") as f:
        json.dump(store, f, indent=2)


def update_and_filter(scored_opportunities: list[dict]) -> list[dict]:
    """
    scored_opportunities: list of dicts with at least
        {"theme_key": str, "overall_score": float, ...}

    Returns only the ones worth telling the user about today:
    - brand new themes, or
    - themes whose mention count has grown since last seen
    Every theme's running mention count is updated in the store either way.
    """
    store = load_store()
    today = datetime.now(timezone.utc).date().isoformat()
    to_report = []

    for opp in scored_opportunities:
        key = opp["theme_key"]
        prior = store.get(key)

        if prior is None:
            store[key] = {
                "first_seen": today,
                "last_seen": today,
                "mention_count": 1,
                "best_score": opp["overall_score"],
            }
            opp["status"] = "NEW"
            to_report.append(opp)
        else:
            prior["mention_count"] += 1
            prior["last_seen"] = today
            prior["best_score"] = max(prior["best_score"], opp["overall_score"])
            # Only re-surface if it's trending (more mentions since last time)
            if today != prior.get("last_reported_on"):
                opp["status"] = f"TRENDING (seen {prior['mention_count']}x total)"
                to_report.append(opp)
            store[key] = prior

        store[key]["last_reported_on"] = today

    save_store(store)
    return to_report
