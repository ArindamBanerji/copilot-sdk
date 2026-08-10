# Build Your Own Copilot

This Level-3 template uses one harness with two neutral domain skins:

```powershell
python -m examples.build_your_own.run --domain email --decisions 50
python -m examples.build_your_own.run --domain reading --decisions 50
python -m examples.build_your_own.run --domain email --ungoverned --decisions 50
```

The governed path uses the SDK's `CompoundingScorer`, SQLite graph store,
verified outcomes, conservation state, and promotion gate. `--ungoverned`
uses a faithful contextual LinUCB reward maximizer with the same metadata and
reward asymmetry, but no centroid decision or conservation gate.

Open `report.html` after a run. The domain files are intentionally small:
copy one, change its actions/factors/asymmetry, and keep the harness.
See [TUTORIAL.md](TUTORIAL.md) for the porting walkthrough.
