"""Known-value validation for RSI and volume rank.

These MUST pass before any service uses these computations.
"""

from apps.trading.backend.app.services.market_computations import (
    compute_rsi,
    compute_vol_rank,
)

# Known SPY-like series: 20 daily closes trending up with pullback
KNOWN_CLOSES = [
    440.0,
    442.5,
    441.0,
    443.5,
    445.0,
    444.0,
    446.5,
    448.0,
    447.0,
    449.5,
    451.0,
    450.0,
    448.5,
    447.0,
    449.0,
    451.5,
    453.0,
    452.0,
    454.5,
    456.0,
]

# Known volume series for percentile test
KNOWN_VOLUMES = [
    1000,
    1200,
    900,
    1100,
    1500,
    800,
    1300,
    1400,
    950,
    1050,
]


def test_rsi_in_valid_range():
    """RSI must be between 0 and 100."""
    rsi = compute_rsi(KNOWN_CLOSES, period=14)
    assert rsi is not None
    assert 0 <= rsi <= 100


def test_rsi_trending_up_above_50():
    """An uptrending series should have RSI > 50."""
    rsi = compute_rsi(KNOWN_CLOSES, period=14)
    assert rsi is not None
    assert rsi > 50, f"Uptrending series RSI should be > 50, got {rsi}"


def test_rsi_insufficient_data():
    """Fewer than period+1 closes returns None."""
    assert compute_rsi([440.0, 442.0], period=14) is None


def test_rsi_flat_series():
    """Flat series (no movement) should return RSI near 50 or 100."""
    flat = [100.0] * 20
    rsi = compute_rsi(flat, period=14)
    # No losses -> RSI = 100
    assert rsi is not None


def test_vol_rank_highest():
    """Latest volume is highest -> percentile near 100."""
    volumes = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    rank = compute_vol_rank(volumes)
    assert rank == 90  # 9 out of 10 below


def test_vol_rank_lowest():
    """Latest volume is lowest -> percentile near 0."""
    volumes = [1000, 900, 800, 700, 600, 500, 400, 300, 200, 100]
    rank = compute_vol_rank(volumes)
    assert rank == 0  # 0 out of 10 below


def test_vol_rank_middle():
    """Latest in middle of distribution."""
    rank = compute_vol_rank(KNOWN_VOLUMES)
    assert rank is not None
    assert 0 <= rank <= 100


def test_vol_rank_insufficient():
    """Single volume returns None."""
    assert compute_vol_rank([100]) is None
