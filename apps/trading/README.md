# ci-trading

Decision quality analysis for traders. `ci-trading` keeps a local trading journal, imports broker trade exports, scores the context around each trade, and shows which signals have historically predicted your own outcomes.

This v0.1.0 package is an editable-install wrapper for the source checkout. It is not the standalone PyPI distribution yet. Standalone `pip install ci-trading` without a git clone ships in v0.2.0 after import-chain restructuring.

## Install v0.1.0 From Source

```bash
git clone https://github.com/ArindamBanerji/copilot-sdk.git
cd copilot-sdk/apps/trading
pip install -e .
ci-trading init
ci-trading import --file my_trades.csv
ci-trading score
```

The editable install expects the repository checkout to remain in place because the CLI delegates to the existing backend implementation in `apps/trading/backend`.

## Local Data

Data stays local by default under `~/.ci-trading`, unless you pass `--config-dir` to point the CLI at another directory.

## Optional Broker Integrations

The default CSV workflow has no broker SDK requirement. Optional integrations remain optional:

```bash
pip install -e ".[ibkr]"
pip install -e ".[alpaca]"
pip install -e ".[market-data]"
```

## License

Apache License 2.0. See `LICENSE`.

## Disclaimer

`ci-trading` does not provide investment advice. It does not provide trading signals or recommendations. It analyzes your recorded decisions and outcomes for journaling and decision-quality review only. Past performance does not predict future results. Consult a qualified financial advisor before making investment or trading decisions.
