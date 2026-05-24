import os
from alpaca.trading.client import TradingClient

client = TradingClient(
    os.environ["APCA_API_KEY_ID"],
    os.environ["APCA_API_SECRET_KEY"],
    paper=True,
)
acct = client.get_account()
print("Status:", acct.status)
print("Buying power:", acct.buying_power)
print("Cash:", acct.cash)
