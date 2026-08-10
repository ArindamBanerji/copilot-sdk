# Level-2 YAML configuration

This is the 30-minute path for a domain owner who wants to configure a
copilot without writing Python domain code.

1. Install the SDK and PyYAML (`pip install pyyaml`).
2. Copy `domain.yaml` and change `from`, `penalty_ratio`, or factor weights.
3. Run it from `copilot-sdk`:

   ```text
   python -m examples.yaml_config.run examples/yaml_config/domain.yaml
   ```

The loader starts from a built-in SDK preset, validates the YAML mapping, and
builds the real `CompoundingScorer`. The example then runs the normal SDK
`score` → outcome → `learn` loop. `thesis_conviction` maps to the trading
preset's canonical `signal_confidence`; `risk_reward` maps to
`risk_reward_actual`.

The same loop is deterministic for a given seed, so a Python mapping with the
same values produces the same decisions as the YAML mapping.
