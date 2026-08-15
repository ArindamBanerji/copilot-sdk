from __future__ import annotations

from typing import Any

from copilot_sdk.graph import ProtocolV2OutcomeService, SQLiteGraphStore
from copilot_sdk.graph.outbox import DurableOutbox


DOMAIN = "protocol-v2-service"


class UnavailableAgeWriter:
    """External AGE boundary that is unavailable for the pending-sync tests."""

    def __call__(self, *args: object, **kwargs: object) -> None:
        raise ConnectionError("AGE unavailable")


def _service(tmp_path, *, writer: Any = None):
    store = SQLiteGraphStore(tmp_path / "protocol-v2.sqlite", domain=DOMAIN)
    store.write_governed_decision(
        "DEC-1",
        DOMAIN,
        "category",
        0,
        "approve",
        0,
        0.9,
        [0.9, 0.1],
        [0.2, 0.8],
        ["factor_a", "factor_b"],
        metadata={"created_at": 1.0},
    )
    store.update_conservation_state(
        DOMAIN,
        "GREEN",
        0.5,
        0.5,
        0,
        0.1,
        0.25,
        1,
        0,
        0.25,
        0.1,
        "false",
    )
    outbox = DurableOutbox(str(tmp_path / "outbox.sqlite"))
    service = ProtocolV2OutcomeService(
        store,
        domain=DOMAIN,
        outbox=outbox,
        canonical_writer=writer,
    )
    return service, store, outbox


def _close(store: SQLiteGraphStore, outbox: DurableOutbox) -> None:
    outbox.close()
    store.close()


def test_api_learn_committed():
    """Service layer returns committed when AGE write_outcome succeeds."""
    # Protocol v2 service-layer invariant: committed means canonical store commit.
    # The SQLite writer is the real canonical transaction boundary.
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        service, store, outbox = _service(Path(directory))
        try:
            result = service.learn("DEC-1", "approve", True)

            assert result["status"] == "committed"
            assert result["canonical_committed"] is True
            assert store.count_verified_decisions(DOMAIN) == 1
            assert store.get_conservation_state(DOMAIN)["V"] == 1
            assert outbox.pending_count() == 0
        finally:
            _close(store, outbox)


def test_api_learn_pending_sync():
    """Service layer returns accepted_pending_sync when AGE is unavailable."""
    # Protocol v2 service-layer invariant: outbox fallback lives above GraphStore.
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        service, store, outbox = _service(
            Path(directory), writer=UnavailableAgeWriter()
        )
        try:
            result = service.learn("DEC-1", "approve", True)

            assert result["status"] == "accepted_pending_sync"
            assert result["canonical_committed"] is False
            assert store.count_verified_decisions(DOMAIN) == 0
            assert outbox.pending_count() == 1
        finally:
            _close(store, outbox)


def test_pending_sync_no_V_increment():
    """accepted_pending_sync does not increment conservation V before replay."""
    # Protocol v2 service-layer invariant: V updates only after canonical commit.
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        service, store, outbox = _service(
            Path(directory), writer=UnavailableAgeWriter()
        )
        try:
            result = service.learn("DEC-1", "approve", True)

            assert result["status"] == "accepted_pending_sync"
            assert result["V"] == 0
            assert store.get_conservation_state(DOMAIN)["V"] == 0
        finally:
            _close(store, outbox)


def test_replay_then_V_increments():
    """Outbox replay commits the outcome and then increments V."""
    # Protocol v2 service-layer invariant: replay changes V after successful commit.
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        service, store, outbox = _service(
            Path(directory), writer=UnavailableAgeWriter()
        )
        try:
            service.learn("DEC-1", "approve", True)
            service.set_canonical_writer(store.write_outcome)

            first = service.replay()
            second = service.replay()

            assert first == {"replayed": 1, "failed": 0, "remaining": 0, "V": 1}
            assert second == {"replayed": 0, "failed": 0, "remaining": 0, "V": 1}
            assert store.count_verified_decisions(DOMAIN) == 1

            outbox.append(
                "write_outcome",
                DOMAIN,
                {
                    "args": ["DEC-1", "reject", False],
                    "kwargs": {"metadata": {}, "domain": DOMAIN},
                },
                "conflicting replay",
            )
            conflict = service.replay()
            assert conflict["failed"] == 1
            assert outbox.failed_count() == 1
            failed_id = outbox.get_pending(limit=1)
            assert failed_id == []
            # A conflicting replay is reviewable and can be explicitly quarantined.
            import sqlite3

            connection = sqlite3.connect(str(Path(directory) / "outbox.sqlite"))
            row = connection.execute(
                "SELECT id FROM secondary_outbox WHERE status = 'failed'"
            ).fetchone()
            connection.close()
            assert row is not None
            outbox.quarantine_failed(int(row[0]))
            assert outbox.unresolved_count() == 0
        finally:
            _close(store, outbox)
