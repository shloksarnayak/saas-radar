"""
Sends raw collected posts/comments to Claude in batches. Claude:
  1. filters out noise (not every post with a keyword match is a real pain point)
  2. extracts a normalized "theme" (so duplicates across sources merge)
  3. scores it 0-10 on: payment_signal, frequency_signal, competition_gap
  4. uses web search to sanity-check whether obvious existing tools already solve it

Needs env var: ANTHROPIC_API_KEY
"""
import os
import json
import anthropic
from config import MAX_ITEMS_PER_RUN, MIN_SCORE_TO_REPORT

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are a market-research analyst for a bootstrapped SaaS founder.
You will be given a batch of raw, informal posts/comments scraped from Reddit and \
Hacker News. Each one matched a keyword suggesting a complaint or unmet need, but many \
are noise (jokes, unrelated context, vague venting with no real problem).

For each item that describes a GENUINE, SPECIFIC recurring problem someone has \
(not vague venting), do the following:
1. Write a short normalized "theme_key" (3-6 words, lowercase, hyphenated) that would be \
   IDENTICAL for two posts describing the same underlying problem, so duplicates merge.
2. Write a one-sentence plain-English description of the problem.
3. Use web search briefly if useful to sanity-check whether well-known SaaS tools already \
   solve this well (affects competition_gap score).
4. Score 0-10 on each:
   - payment_signal: evidence people already pay for a workaround / manual service / spreadsheet
   - frequency_signal: how often this specific complaint seems to recur in general (not just this batch)
   - competition_gap: how open the space is (10 = no good existing tools, 0 = saturated/solved well)
5. Compute overall_score as the average of the three, rounded to 1 decimal.

Discard anything vague, one-off, or not plausibly solvable by a small SaaS product.

Return ONLY a JSON array (no markdown, no prose) of objects with exactly these keys:
theme_key, description, payment_signal, frequency_signal, competition_gap, overall_score, evidence_quote (<15 words, paraphrase not verbatim), source_url
"""


def _chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def score_items(raw_items: list[dict]) -> list[dict]:
    if not raw_items:
        return []

    raw_items = raw_items[:MAX_ITEMS_PER_RUN]
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    results = []
    for batch in _chunk(raw_items, 20):
        batch_payload = [
            {"url": it["url"], "source": it["source"], "text": it["text"]}
            for it in batch
        ]

        message = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{
                "role": "user",
                "content": f"Batch of {len(batch)} items:\n\n{json.dumps(batch_payload, indent=2)}"
            }],
        )

        # Pull out only the final text block(s); web_search tool_use/tool_result
        # blocks are handled server-side and interleaved automatically.
        text_out = "".join(
            block.text for block in message.content if block.type == "text"
        ).strip()

        # Be lenient about accidental markdown fencing
        text_out = text_out.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(text_out)
            results.extend(parsed)
        except json.JSONDecodeError:
            print("[scorer] could not parse a batch response, skipping it:")
            print(text_out[:500])
            continue

    scored = [r for r in results if r.get("overall_score", 0) >= MIN_SCORE_TO_REPORT]
    scored.sort(key=lambda x: x["overall_score"], reverse=True)
    return scored
