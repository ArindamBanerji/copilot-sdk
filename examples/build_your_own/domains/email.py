"""Email/inbox triage domain skin.

Only synthetic metadata is used; no message content is represented.
"""

DOMAIN_NAME = "email_triage"
ACTIONS = ["priority", "normal", "archive"]
CATEGORIES = ["work", "personal", "newsletter"]
FACTORS = [
    "sender_frequency",
    "thread_depth",
    "subject_signal",
    "time_of_day",
    "has_attachment",
    "prior_response_rate",
]
PENALTY_RATIO = 5.0
EPSILON_FIRM = 0.20
HIGH_RISK_CATEGORIES = ["work"]
POISONED_RULE_DESCRIPTION = "auto-archive rare senders"
