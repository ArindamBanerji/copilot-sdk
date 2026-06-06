from __future__ import annotations

import pytest


pytestmark = pytest.mark.skip(reason="Protocol v2 implementation pending")


def test_api_learn_committed():
    """Service layer returns committed when AGE write_outcome succeeds."""
    # Protocol v2 service-layer invariant: committed means canonical store commit.
    pass


def test_api_learn_pending_sync():
    """Service layer returns accepted_pending_sync when AGE is unavailable."""
    # Protocol v2 service-layer invariant: outbox fallback lives above GraphStore.
    pass


def test_pending_sync_no_V_increment():
    """accepted_pending_sync does not increment conservation V before replay."""
    # Protocol v2 service-layer invariant: V updates only after canonical commit.
    pass


def test_replay_then_V_increments():
    """Outbox replay commits the outcome and then increments V."""
    # Protocol v2 service-layer invariant: replay changes V after successful commit.
    pass
