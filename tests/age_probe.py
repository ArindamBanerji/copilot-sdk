"""Driver spy for migrations: every read and write executes against disposable AGE."""
from __future__ import annotations

from typing import Any
import re

from ci_platform.graph.age_client import AGEClient


class MigrationProbe:
    def __init__(self, environment: Any, *, fail_on_decision_create: int | None = None) -> None:
        self.environment = environment
        self.graph = environment.graph
        self.dsn = environment.dsn
        self.connection: Any = None
        self.fail_on_decision_create = fail_on_decision_create
        self.decision_creates = 0
        self.commits = 0
        self.rollbacks = 0
        self.queries: list[str] = []
        self.closed = True
        self.open()

    def open(self) -> MigrationProbe:
        if self.closed:
            self.connection = self.environment.connect()
            self.connection.autocommit = False
            self.closed = False
        return self

    def execute(self, query: str, *args: Any, **kwargs: Any) -> Any:
        self.queries.append(query)
        if "CREATE (d:Decision" in query:
            self.decision_creates += 1
            if self.decision_creates == self.fail_on_decision_create:
                raise RuntimeError("injected batch failure")
        return self.connection.execute(query, *args, **kwargs)

    def commit(self) -> None:
        self.connection.commit()
        self.commits += 1

    def rollback(self) -> None:
        self.connection.rollback()
        self.rollbacks += 1

    def close(self) -> None:
        if not self.closed:
            self.connection.close()
            self.closed = True

    @property
    def commit_count(self) -> int:
        return self.commits

    @property
    def rollback_count(self) -> int:
        return self.rollbacks

    def read(self, query: str) -> list[dict[str, Any]]:
        store = self.environment.store("trading")
        try:
            return list(store._store._run_query(query))
        finally:
            store.close()

    def seed_node(self, label: str, properties: dict[str, Any]) -> None:
        assert label in {"Decision", "Outcome", "EvidenceReceipt", "CentroidCheckpoint", "Domain"}
        assert all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) for key in properties)
        literal = "{" + ", ".join(
            f"{key}: {AGEClient.serialize_for_age(value)}" for key, value in properties.items()
        ) + "}"
        self.read(f"CREATE (n:{label} {literal}) RETURN n")

    @property
    def nodes(self) -> list[dict[str, Any]]:
        output = []
        for label in ("Decision", "Outcome", "EvidenceReceipt", "CentroidCheckpoint"):
            for row in self.read(f"MATCH (n:{label}) RETURN properties(n) AS props"):
                output.append({**row["props"], "label": label})
        return output

    @property
    def edges(self) -> list[dict[str, Any]]:
        output = []
        for label in ("HAS_OUTCOME", "HAS_CENTROID_CHECKPOINT", "EMITTED_RECEIPT"):
            for row in self.read(f"MATCH (a)-[r:{label}]->(b) RETURN properties(b) AS target"):
                output.append({**row["target"], "label": label})
        return output
