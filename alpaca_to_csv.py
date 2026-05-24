"""
alpaca_to_csv.py — Export Alpaca orders to CSV for ci-trading import.

Usage:
    python alpaca_to_csv.py                    # export all closed orders
    python alpaca_to_csv.py --days 30          # last 30 days only
    python alpaca_to_csv.py --output my.csv    # custom output path

Then:
    ci-trading import --file alpaca_trades.csv
"""
import os
import sys
import csv
import argparse
from datetime import datetime, timedelta, timezone

API_KEY = os.environ.get("APCA_API_KEY_ID")
API_SECRET = os.environ.get("APCA_API_SECRET_KEY")

if not API_KEY or not API_SECRET:
    print("ERROR: Alpaca credentials not in environment.")
    print("  Open a NEW PowerShell window (User-scope vars load on start).")
    sys.exit(1)

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus


def export_orders(days: int | None = None, output: str = "alpaca_trades.csv"):
    client = TradingClient(API_KEY, API_SECRET, paper=True)

    # Verify connection
    acct = client.get_account()
    print(f"Connected: {acct.status}, cash=${float(acct.cash):,.2f}")

    # Fetch closed (filled) orders
    params = {"status": QueryOrderStatus.CLOSED, "limit": 500}
    if days:
        after = datetime.now(timezone.utc) - timedelta(days=days)
        params["after"] = after

    request = GetOrdersRequest(**params)
    orders = client.get_orders(filter=request)

    if not orders:
        print("No closed orders found.")
        return

    # Filter to filled only
    filled = [o for o in orders if str(o.status).lower() == "filled"]
    print(f"Found {len(filled)} filled orders.")

    # Write CSV in ci-trading expected format
    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date", "ticker", "direction", "qty", "price",
            "strategy_tag", "notes", "broker"
        ])
        for o in filled:
            writer.writerow([
                str(o.filled_at or o.submitted_at)[:19],  # ISO datetime
                o.symbol,
                "long" if str(o.side) == "OrderSide.BUY" else "short",
                str(o.filled_qty or o.qty),
                str(o.filled_avg_price or ""),
                "",   # strategy_tag: user can retag later
                f"Alpaca paper {o.id}",
                "alpaca",
            ])

    print(f"Exported {len(filled)} trades to {output}")
    print(f"\nNext:")
    print(f"  ci-trading import --file {output}")
    print(f"  ci-trading journal")
    print(f"  ci-trading score")


def main():
    parser = argparse.ArgumentParser(description="Export Alpaca to CSV")
    parser.add_argument("--days", type=int, help="Last N days only")
    parser.add_argument("--output", default="alpaca_trades.csv")
    args = parser.parse_args()
    export_orders(days=args.days, output=args.output)


if __name__ == "__main__":
    main()
