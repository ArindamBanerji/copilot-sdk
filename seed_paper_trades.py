"""
seed_paper_trades.py — Place 25 varied paper trades on Alpaca.

Run from PowerShell where APCA_API_KEY_ID and APCA_API_SECRET_KEY
are set as environment variables.

Usage:
    python seed_paper_trades.py              # place + close trades
    python seed_paper_trades.py --status     # check account + positions
    python seed_paper_trades.py --dry-run    # show plan without trading

What it does:
  1. Places 25 market orders across 15 tickers (varied sectors)
  2. Waits for fills
  3. Closes 20 of them (creates completed trades with P&L)
  4. Leaves 5 open (swing positions for later analysis)

After running:
    ci-trading import --broker alpaca --days 30
    ci-trading journal
    ci-trading score
    ci-trading trust
"""
import os
import sys
import time
import argparse
from datetime import datetime

# ── Credential check ─────────────────────────────────────────────
API_KEY = os.environ.get("APCA_API_KEY_ID")
API_SECRET = os.environ.get("APCA_API_SECRET_KEY")

if not API_KEY or not API_SECRET:
    print("ERROR: Alpaca credentials not found in environment.")
    print("  APCA_API_KEY_ID:     ", "SET" if API_KEY else "MISSING")
    print("  APCA_API_SECRET_KEY: ", "SET" if API_SECRET else "MISSING")
    print()
    print("These must be Windows User-scope env vars.")
    print("Open a NEW PowerShell window (env vars load on process start).")
    print("Do NOT hardcode credentials. Do NOT create .env files.")
    sys.exit(1)

# ── Imports (after credential check) ─────────────────────────────
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, ClosePositionRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus


# ── Trade Plan ───────────────────────────────────────────────────
# 25 trades across 15 tickers, 5 categories, varied sizes.
# "close" = close immediately (day trade / scalp).
# "hold"  = leave open (swing position for later).

TRADE_PLAN = [
    # ── Cluster A: Trend Following (7 trades) ────────────────────
    {"ticker": "AAPL",  "side": "buy",  "qty": 15, "tag": "trend_following",  "action": "close"},
    {"ticker": "MSFT",  "side": "buy",  "qty": 10, "tag": "trend_following",  "action": "close"},
    {"ticker": "NVDA",  "side": "buy",  "qty": 5,  "tag": "trend_following",  "action": "hold"},
    {"ticker": "META",  "side": "buy",  "qty": 8,  "tag": "trend_following",  "action": "close"},
    {"ticker": "AMZN",  "side": "buy",  "qty": 6,  "tag": "trend_following",  "action": "close"},
    {"ticker": "GOOGL", "side": "buy",  "qty": 10, "tag": "trend_following",  "action": "close"},
    {"ticker": "TSLA",  "side": "buy",  "qty": 5,  "tag": "trend_following",  "action": "hold"},

    # ── Cluster B: Mean Reversion (5 trades) ─────────────────────
    {"ticker": "JPM",   "side": "buy",  "qty": 8,  "tag": "mean_reversion",   "action": "close"},
    {"ticker": "BAC",   "side": "buy",  "qty": 25, "tag": "mean_reversion",   "action": "close"},
    {"ticker": "XOM",   "side": "buy",  "qty": 10, "tag": "mean_reversion",   "action": "close"},
    {"ticker": "CVX",   "side": "buy",  "qty": 8,  "tag": "mean_reversion",   "action": "close"},
    {"ticker": "DIS",   "side": "buy",  "qty": 12, "tag": "mean_reversion",   "action": "hold"},

    # ── Cluster C: Event Driven (4 trades) ───────────────────────
    {"ticker": "AMD",   "side": "buy",  "qty": 10, "tag": "event_driven",     "action": "close"},
    {"ticker": "NFLX",  "side": "buy",  "qty": 3,  "tag": "event_driven",     "action": "close"},
    {"ticker": "CRM",   "side": "buy",  "qty": 5,  "tag": "earnings_direction","action": "close"},
    {"ticker": "ORCL",  "side": "buy",  "qty": 8,  "tag": "earnings_vol",     "action": "close"},

    # ── Cluster D: Income / Short (5 trades) ─────────────────────
    # Alpaca paper supports short selling
    {"ticker": "SPY",   "side": "sell", "qty": 5,  "tag": "income_strategy",  "action": "close"},
    {"ticker": "QQQ",   "side": "sell", "qty": 5,  "tag": "income_strategy",  "action": "close"},
    {"ticker": "IWM",   "side": "sell", "qty": 10, "tag": "income_strategy",  "action": "close"},
    {"ticker": "AAPL",  "side": "sell", "qty": 5,  "tag": "income_strategy",  "action": "hold"},
    {"ticker": "MSFT",  "side": "sell", "qty": 5,  "tag": "income_strategy",  "action": "close"},

    # ── Cluster E: Scalp / Intraday (4 trades) ──────────────────
    {"ticker": "SPY",   "side": "buy",  "qty": 20, "tag": "scalp_intraday",   "action": "close"},
    {"ticker": "QQQ",   "side": "buy",  "qty": 15, "tag": "scalp_intraday",   "action": "close"},
    {"ticker": "NVDA",  "side": "buy",  "qty": 3,  "tag": "scalp_intraday",   "action": "close"},
    {"ticker": "AMD",   "side": "buy",  "qty": 10, "tag": "scalp_intraday",   "action": "hold"},
]


def show_status(client: TradingClient):
    """Show account status and open positions."""
    acct = client.get_account()
    print(f"\n=== Alpaca Paper Account ===")
    print(f"  Status:       {acct.status}")
    print(f"  Cash:         ${float(acct.cash):,.2f}")
    print(f"  Buying Power: ${float(acct.buying_power):,.2f}")
    print(f"  Equity:       ${float(acct.equity):,.2f}")
    print(f"  P&L Today:    ${float(acct.equity) - float(acct.last_equity):,.2f}")

    positions = client.get_all_positions()
    if positions:
        print(f"\n  Open Positions ({len(positions)}):")
        for p in positions:
            side = "LONG" if float(p.qty) > 0 else "SHORT"
            pnl = float(p.unrealized_pl)
            print(f"    {p.symbol:<6} {side:<5} {abs(float(p.qty)):>6.0f} shares  "
                  f"avg ${float(p.avg_entry_price):>8.2f}  P&L ${pnl:>8.2f}")
    else:
        print(f"\n  No open positions.")

    orders = client.get_orders()
    closed = client.get_orders(filter={"status": "closed", "limit": 5})
    print(f"\n  Open orders:  {len(orders)}")
    print(f"  Recent closed: {len(closed)}")
    return acct


def place_and_close(client: TradingClient, dry_run: bool = False):
    """Execute the trade plan."""
    print(f"\n=== Trade Plan: {len(TRADE_PLAN)} trades ===")
    close_count = sum(1 for t in TRADE_PLAN if t["action"] == "close")
    hold_count = sum(1 for t in TRADE_PLAN if t["action"] == "hold")
    print(f"  Close immediately: {close_count}")
    print(f"  Hold (swing):      {hold_count}")
    print()

    if dry_run:
        print("DRY RUN — no orders placed.\n")
        for i, t in enumerate(TRADE_PLAN, 1):
            arrow = "BUY " if t["side"] == "buy" else "SELL"
            print(f"  {i:>2}. {arrow} {t['qty']:>3} {t['ticker']:<6} "
                  f"[{t['tag']:<20}] → {t['action']}")
        return

    # ── Phase 1: Place all orders ────────────────────────────────
    print("Phase 1: Placing orders...")
    order_ids = []
    for i, t in enumerate(TRADE_PLAN, 1):
        side = OrderSide.BUY if t["side"] == "buy" else OrderSide.SELL
        req = MarketOrderRequest(
            symbol=t["ticker"],
            qty=t["qty"],
            side=side,
            time_in_force=TimeInForce.DAY,
        )
        try:
            order = client.submit_order(req)
            order_ids.append({
                "order_id": order.id,
                "ticker": t["ticker"],
                "side": t["side"],
                "qty": t["qty"],
                "tag": t["tag"],
                "action": t["action"],
                "status": str(order.status),
            })
            arrow = "BUY " if t["side"] == "buy" else "SELL"
            print(f"  {i:>2}. {arrow} {t['qty']:>3} {t['ticker']:<6} → {order.status}")
        except Exception as e:
            print(f"  {i:>2}. FAILED {t['ticker']}: {e}")
            order_ids.append(None)
        time.sleep(0.3)  # rate limit courtesy

    # ── Phase 2: Wait for fills ──────────────────────────────────
    print(f"\nPhase 2: Waiting for fills...")
    max_wait = 60  # seconds
    start = time.time()
    while time.time() - start < max_wait:
        pending = 0
        for entry in order_ids:
            if entry is None:
                continue
            if entry["status"] not in ("filled", "FILLED", "canceled", "CANCELED"):
                try:
                    order = client.get_order_by_id(entry["order_id"])
                    entry["status"] = str(order.status)
                    if str(order.status).lower() == "filled":
                        entry["filled_price"] = str(order.filled_avg_price)
                except Exception:
                    pass
                if entry["status"].lower() not in ("filled", "canceled"):
                    pending += 1
        if pending == 0:
            break
        print(f"  {pending} orders pending... ({int(time.time() - start)}s)")
        time.sleep(2)

    filled = sum(1 for e in order_ids if e and e["status"].lower() == "filled")
    print(f"\n  Filled: {filled}/{len(TRADE_PLAN)}")

    # ── Phase 3: Close positions marked "close" ──────────────────
    print(f"\nPhase 3: Closing {close_count} positions...")
    time.sleep(2)  # brief pause before closing

    # Group by ticker to handle net positions
    to_close = {}
    for entry in order_ids:
        if entry is None or entry["action"] != "close":
            continue
        if entry["status"].lower() != "filled":
            continue
        ticker = entry["ticker"]
        if ticker not in to_close:
            to_close[ticker] = {"buy_qty": 0, "sell_qty": 0}
        if entry["side"] == "buy":
            to_close[ticker]["buy_qty"] += entry["qty"]
        else:
            to_close[ticker]["sell_qty"] += entry["qty"]

    closed_count = 0
    for ticker, qtys in to_close.items():
        # Close each side separately
        try:
            # Check current position
            try:
                pos = client.get_open_position(ticker)
                pos_qty = float(pos.qty)
            except Exception:
                print(f"  {ticker}: no position to close")
                continue

            # Close the position (or partial)
            if abs(pos_qty) > 0:
                # Determine how much to close vs hold
                hold_qty = 0
                for entry in order_ids:
                    if entry and entry["ticker"] == ticker and entry["action"] == "hold":
                        if entry["side"] == "buy":
                            hold_qty += entry["qty"]
                        else:
                            hold_qty -= entry["qty"]

                close_qty = abs(pos_qty) - abs(hold_qty)
                if close_qty > 0:
                    close_side = OrderSide.SELL if pos_qty > 0 else OrderSide.BUY
                    req = MarketOrderRequest(
                        symbol=ticker,
                        qty=close_qty,
                        side=close_side,
                        time_in_force=TimeInForce.DAY,
                    )
                    order = client.submit_order(req)
                    print(f"  {ticker:<6} closing {close_qty} shares → {order.status}")
                    closed_count += 1
                    time.sleep(0.3)
        except Exception as e:
            print(f"  {ticker}: close failed: {e}")

    # ── Phase 4: Wait for close fills ────────────────────────────
    print(f"\n  Waiting for close fills...")
    time.sleep(5)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n=== Summary ===")
    print(f"  Orders placed:  {len(TRADE_PLAN)}")
    print(f"  Filled:         {filled}")
    print(f"  Closed:         {closed_count} tickers")
    print(f"  Held (swing):   {hold_count} positions")

    # Show final state
    show_status(client)

    print(f"\n=== Next Steps ===")
    print(f"  1. Wait a few minutes for settlements")
    print(f"  2. Run: ci-trading import --broker alpaca --days 30")
    print(f"  3. Run: ci-trading journal")
    print(f"  4. Run: ci-trading score")
    print(f"  5. Run: ci-trading trust")


def main():
    parser = argparse.ArgumentParser(description="Seed Alpaca paper trades")
    parser.add_argument("--status", action="store_true",
                        help="Show account status only")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show trade plan without placing orders")
    args = parser.parse_args()

    client = TradingClient(API_KEY, API_SECRET, paper=True)

    # Verify connection
    try:
        acct = client.get_account()
        print(f"Connected to Alpaca Paper. Status: {acct.status}")
    except Exception as e:
        print(f"ERROR: Cannot connect to Alpaca: {e}")
        sys.exit(1)

    if args.status:
        show_status(client)
        return

    if args.dry_run:
        place_and_close(client, dry_run=True)
        return

    # Safety check
    print(f"\nThis will place {len(TRADE_PLAN)} paper trades on your account.")
    confirm = input("Continue? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    place_and_close(client)


if __name__ == "__main__":
    main()
