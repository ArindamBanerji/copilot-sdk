"""Mock weather connector for purchasing demos and tests."""

from __future__ import annotations

from datetime import date, timedelta


class MockWeatherConnector:
    """Test double. Seven days of fixture data. No network."""

    def fetch(self, entity_id: str = "7day") -> list[dict]:
        del entity_id
        today = date.today()
        rows = [
            ("Today", "calm", 72, 10, "LOW"),
            ("Tomorrow", "storm", 48, 90, "HIGH"),
            ("Day 3", "heat", 94, 5, "MODERATE"),
            ("Day 4", "calm", 70, 15, "LOW"),
            ("Day 5", "rain", 55, 70, "MODERATE"),
            ("Day 6", "calm", 68, 20, "LOW"),
            ("Day 7", "calm", 74, 10, "LOW"),
        ]
        return [
            {
                "label": label,
                "date": (today + timedelta(days=index)).isoformat(),
                "condition": condition,
                "temperature_f": temp,
                "precipitation_prob": precip,
                "risk": risk,
                "source": "OpenMeteo",
            }
            for index, (label, condition, temp, precip, risk) in enumerate(rows)
        ]
