# B32 Loom Recording Gauntlet

`scripts/loom_gauntlet.py` is the standalone recording runner for the B31
hero moments. It executes the available preseed and truth-preflight stages,
runs C2 through C5 for each configured copilot, captures timing and
before/after state, and writes two artifacts:

- `docs/loom_gauntlet_report.json` — machine-readable run report.
- `docs/loom_storyboard_v1.md` — five-act Loom script with timestamps,
  talking points, show guidance, and expected output.

## Usage

```text
python scripts/loom_gauntlet.py --help
python scripts/loom_gauntlet.py --skip-preseed --json
python scripts/loom_gauntlet.py --copilots trading purchasing --skip-preseed
```

The default ports are SOC `8001`, S2P `8002`, Trading `8010`, Purchasing
`8020`, and DataOps `8030`. `SOC_URL`, `S2P_URL`, `TRADING_URL`,
`PURCHASING_URL`, and `DATAOPS_URL` can override the local URLs used by the
hero runner.

## Sequence

1. Preseed all available copilots through `preseed_all_copilots.py`.
2. Run `demo_truth_preflight.py`.
3. Run C2, C3, C4, and C5 for each selected copilot.
4. Capture elapsed time, evidence paths, IKS values when exposed, and raw
   before/after state.
5. Generate the five-act storyboard.

Missing services and unsupported contracts are recorded as statuses rather
than treated as successful demo beats. The storyboard explicitly instructs
the presenter not to narrate those states as achievements.

## Scope limitation

This implementation does not edit `demo.py` or add tests because the task
scope permits only `scripts/` and `docs/`. Consequently, `demo.py --loom`
integration and LG-01–LG-15 automated test coverage remain follow-up work when
those paths are authorized. The gauntlet itself is independently executable.
