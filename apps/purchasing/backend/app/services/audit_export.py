"""Demo audit export service for purchasing decisions."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any


class AuditExportService:
    """SOX-adjacent audit pack from existing evidence."""

    def generate_pack(self, period: str = "last_quarter") -> dict[str, Any]:
        decision_trail = [
            {"decision_id": "PUR-001", "timestamp": "2026-04-02T12:00:00Z", "action": "approve", "override": False, "reason": "Par level within tolerance."},
            {"decision_id": "PUR-002", "timestamp": "2026-04-09T12:00:00Z", "action": "hold", "override": True, "reason": "Chef override during event week."},
            {"decision_id": "PUR-003", "timestamp": "2026-04-16T12:00:00Z", "action": "approve", "override": False, "reason": "Supplier delivery confirmed."},
        ]
        override_history = [row for row in decision_trail if row["override"]]
        sections = {
            "decision_trail": decision_trail,
            "conservation_proof": {"status": "GREEN", "window": period, "summary": "Conservation GREEN throughout."},
            "override_history": override_history,
            "auto_approve_log": [{"count": 842, "policy": "par_level_safe_order"}],
            "hash_chain_verification": {"verified": True, "hash": "a3f2b89c41d7e009"},
        }
        return {
            "period": period,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sections": sections,
            "total_decisions": 842,
            "total_overrides": 23,
            "override_rate": 23 / 842,
            "narrative": "Q2 Audit Pack: 842 order decisions. 23 overrides (2.7%). Conservation GREEN throughout. Hash chain verified. Ready for quarterly review.",
            "provenance": "demo",
        }

    def export_json(self, period: str = "last_quarter") -> str:
        return json.dumps(self.generate_pack(period), sort_keys=True)

    def export_csv_summary(self, period: str = "last_quarter") -> str:
        pack = self.generate_pack(period)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["decision_id", "timestamp", "action", "override", "reason"])
        writer.writeheader()
        writer.writerows(pack["sections"]["decision_trail"])
        return output.getvalue()
