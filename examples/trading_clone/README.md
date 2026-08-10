# Clone and Compound: Trading Edition

This is the paper-only Trading variant of the Judgment Memory reference app.
It uses the actual SDK Trading preset with synthetic market factor vectors,
SQLite persistence, and no server or credentials.

```powershell
python -m examples.trading_clone.run --decisions 50 --output-dir .\trading_clone_output
```

The generator emits factor vectors only. A separate ground-truth oracle labels
whether the scorer's selected action matches the hidden Trading centroid. The
oracle is the only correctness authority; no generated row supplies its own
correctness label.

The output contains `report.json` and a self-contained `report.html` showing
the clone's centroid, IKS, conservation, measurement, and evolution surfaces.
This example is synthetic paper analysis only and does not connect to brokers,
market APIs, credentials, or live trading.
