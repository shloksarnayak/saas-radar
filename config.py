"""
Central config — edit this file to tune what the radar looks for.
No code changes needed elsewhere if you just want to add/remove sources or keywords.
"""

# Subreddits to scan for pain points. Add/remove freely.
SUBREDDITS = [
    "SaaS", "startups", "Entrepreneur", "smallbusiness", "sideproject",
    "indiehackers", "freelance", "digitalnomad", "ecommerce", "marketing",
    "productivity", "webdev", "AskManagers", "consulting",
]

# Phrases that tend to precede a real, specific complaint.
# Reddit posts/comments are kept only if they contain at least one of these.
COMPLAINT_SIGNALS = [
    "i hate that", "so annoying that", "wish there was a tool",
    "wish there was an app", "does anyone know a tool", "i built a spreadsheet to",
    "i pay someone to", "i still do this manually", "i use excel to",
    "is there a saas for", "is there software that", "any tool that can",
    "i'd pay for", "i would pay for", "someone should build",
    "why is there no tool", "the biggest pain point", "we manually",
    "takes me hours to", "switched from", "cancelled my subscription because",
]

# Hacker News search terms (searched via the free Algolia HN API)
HN_QUERIES = [
    "Ask HN tool for", "Ask HN alternative to", "Show HN I built",
    "workflow is painful", "manual process",
]

# How many days back to pull each run (keep small since this runs daily)
LOOKBACK_DAYS = 2

# Max raw items sent to Claude for scoring per run (cost control)
MAX_ITEMS_PER_RUN = 60

# Score threshold (0-10) below which an opportunity is dropped from the digest
MIN_SCORE_TO_REPORT = 6.0
