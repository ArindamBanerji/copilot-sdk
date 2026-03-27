"""
SourceConnector Protocol — connect external data to graph enrichment.
Implementations are domain-specific (Tier 3).
The protocol is open (Tier 2).
"""
from typing import Protocol


class SourceConnector(Protocol):
    source_name:  str
    entity_type:  str
    trust_tier:   int   # 1 (highest) to 3 (lowest)

    def fetch(self, entity_id: str) -> list[dict]: ...
    def validate(self, record: dict) -> bool: ...
