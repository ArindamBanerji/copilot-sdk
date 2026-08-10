"""Reading/watch-later backlog triage domain skin.

Only synthetic metadata is used; no article or media content is represented.
"""

DOMAIN_NAME = "reading_triage"
ACTIONS = ["read_now", "save_for_later", "let_go"]
CATEGORIES = ["article", "video", "podcast"]
FACTORS = [
    "source_quality",
    "length",
    "topic_match",
    "age_in_backlog",
    "prior_finish_rate",
    "recency",
]
PENALTY_RATIO = 4.0
EPSILON_FIRM = 0.20
HIGH_RISK_CATEGORIES = ["article"]
POISONED_RULE_DESCRIPTION = "always surface high-click sources"
