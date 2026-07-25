# Consolidated Graph Configuration v1.1

Status: implementation contract  
Date: 2026-07-25  
Supersedes: `copilot-sdk/docs/design/graph_config_consolidation_v1.md`

## 1. Executive summary

The v1 inventory identified 63 environment names/patterns across five
copilots, launch tooling, phase scripts, and live-test gates. This revision
closes the three blockers: an AGE declaration can never silently resolve to
SQLite, authorization is derived rather than editable, and every effective
field records whether it came from environment, file, or default.

The only sanctioned environment writer during transition is `demo.py` (its
child environment is copied at `copilot-sdk/demo.py:729-739`). Services and
graph-status modules read a typed object. Environment overrides remain
backward compatible, but collisions emit a warning and production never allows
an expected AGE backend to fall back to SQLite.

## 2. Inventory and evidence

The complete v1 inventory remains binding. Generic keys are listed in the SDK
modules at Trading `copilot-sdk/apps/trading/backend/app/graph_status.py:20-26`,
Purchasing `copilot-sdk/apps/purchasing/backend/app/graph_status.py:22-28`,
DataOps `copilot-sdk/apps/dataops/backend/app/graph_status.py:21-27`, and S2P
`s2p-copilot/backend/app/s2p_graph_status.py:19-25`.

Domain settings are read at Trading
`copilot-sdk/apps/trading/backend/app/graph_status.py:81-141,252-289`,
Purchasing `copilot-sdk/apps/purchasing/backend/app/graph_status.py:86-149,302-334`,
DataOps `copilot-sdk/apps/dataops/backend/app/graph_status.py:83-142,253-283`,
and S2P `s2p-copilot/backend/app/s2p_graph_status.py:94-165,275-304`.
SOC settings are read at `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:28,46-48`
and `gen-ai-roi-demo-v4-v50/backend/app/main.py:50-54,180-194,412-417`.
Demo settings are derived/set at `copilot-sdk/demo.py:82-148,729-739`; phase
overrides are read at `copilot-sdk/scripts/phase_config.py:47-68`.

The S2P skip keys are at
`s2p-copilot/backend/tests/test_s2p_active_age_live.py:20-52`,
`s2p-copilot/backend/tests/test_s2p_active_age_parallel.py:22-51`, and
`s2p-copilot/backend/tests/test_s2p_shadow_live_age.py:16-47`. ci-platform gates
are at `ci-platform/tests/test_age_client.py:5,15-18,399-403`,
`ci-platform/tests/test_counter_store_live_age.py:87-92`,
`ci-platform/tests/test_counter_store_route_readiness.py:244-248`, and
`ci-platform/tests/test_age_graph_store_v.py:291-299`. SOC's destructive gate
is `gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:29-32`.

The ten duplicated concepts remain backend, DSN, graph, domain, test mode,
authorization, shadow mode, live opt-in, API endpoint, and runtime safety.

## 3. TOML contract

Create `copilot-sdk/graph_config.toml`. Secrets and operator DSNs are not
committed. **Do not include an `authorized` key.**

```toml
[defaults]
backend = "sqlite"
expected_backend = "sqlite"
dsn = ""
graph = "soc_graph"
age_test_mode = false

[copilot.soc]
domain = "soc"
backend = "age"
expected_backend = "age"
prefix = "SOC-"
graph = "soc_graph"
port = 8001

[copilot.trading]
domain = "trading"
backend = "age"
expected_backend = "age"
prefix = "TRD-"
graph = "soc_graph"
active_test_mode = false
shadow_age = false
port = 8010

[copilot.purchasing]
domain = "purchasing"
backend = "age"
expected_backend = "age"
prefix = "PUR-"
graph = "soc_graph"
active_test_mode = false
shadow_age = false
port = 8020

[copilot.dataops]
domain = "dataops"
backend = "age"
expected_backend = "age"
prefix = "DOPS-"
graph = "soc_graph"
active_test_mode = false
live_age_test = false
port = 8030

[copilot.s2p]
domain = "s2p"
backend = "age"
expected_backend = "age"
prefix = "S2P-"
graph = "soc_graph"
active_test_mode = false
shadow_age = false
port = 8002

[soc]
neo4j_uri = ""
neo4j_user = "neo4j"
neo4j_password = ""
cors_origins = []
narrative_provider = "template"

[test]
scratch_graph_prefix = "soc_graph_test_"
age_integration = false
age_d2_live_gate = false

[test.s2p]
live_age = false
parallel_age = false
shadow_live_age = false

[phase]
domain = "trading"
sqlite_path = ""
api_base = ""
```

`expected_backend` is an explicit contract. If it is `age` and resolution
produces `sqlite`, loading fails unless profile is development and
`CI_ALLOW_SQLITE_FALLBACK=1` is explicitly present. This guard is active from
Step 2. AGE requires a non-empty DSN and graph at load time.

Authorization is computed as `f"{domain}:{graph}"`; the loader never reads a
free-form authorization string. It also asserts the computed pair equals the
selected domain and graph, making a mismatched pair unrepresentable.

## 4. Typed loader

Create `copilot-sdk/copilot_sdk/config/__init__.py` and
`copilot-sdk/copilot_sdk/config/graph_config.py`:

```python
@dataclass(frozen=True)
class GraphConfig:
    domain: str
    backend: Literal["sqlite", "age", "dual_write"]
    expected_backend: Literal["sqlite", "age", "dual_write"]
    dsn: str | None
    graph: str
    prefix: str
    active_test_mode: bool
    shadow_age: bool
    live_age_test: bool
    port: int | None
    sources: dict[str, Literal["env", "file", "default"]]

    @property
    def authorized(self) -> str:
        return f"{self.domain}:{self.graph}"

    @classmethod
    def load(cls, domain: str = "trading", *, profile: str = "production") -> "GraphConfig": ...

    def validate(self, *, profile: str = "production") -> None: ...
```

Resolve paths from `Path(__file__).resolve()` (SDK package location), never
from CWD. Search the new `GRAPH_CONFIG_PATH` override first, then the
SDK-root TOML, then the package-relative template. Record `sources` as
`env`, `file`, or `default` per field. When environment and file values
differ, log WARNING with both values and `winner=env`; redact DSNs, URIs, and
passwords.

Validation errors are stable and actionable: `missing AGE DSN for domain
'<domain>'`, `missing AGE graph for domain '<domain>'`, `expected backend age
but resolved sqlite`, and `domain/graph authorization mismatch: expected
'<domain>:<graph>'`.

Python floor is 3.11 in `copilot-sdk/pyproject.toml:4,23`,
`ci-platform/pyproject.toml:9,26`, and `s2p-copilot/pyproject.toml:4`.
Use `tomllib`; include a guarded `tomli` fallback for embedded Python 3.10
runners without changing the production floor.

## 5. Test contract

Implement one `is_live_age_configured(domain)` helper that loads typed config,
checks the explicit live opt-in, and verifies scratch graph safety. Keep
`TEST_DESTRUCTIVE_AGE` environment-only as required by
`gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:29-32`.
Print-config displays each value and `sources[field]`, redacting DSN, URI, and
password. CI loads all five domains and asserts no expected-backend failure and
that authorization is derived.

## 6. Detailed implementation steps

### Step 1: TOML, loader, validation, and tests

Files to create: `copilot-sdk/graph_config.toml`,
`copilot-sdk/copilot_sdk/config/__init__.py`,
`copilot-sdk/copilot_sdk/config/graph_config.py`, and
`copilot-sdk/tests/test_graph_config.py`.

In `graph_config.py`, implement the dataclass, `load`, `validate`, TOML search,
tomllib/tomli fallback, env mapping, source tracking, collision logging,
redaction, derived authorization, and expected-backend guard. `__init__.py`
re-exports `GraphConfig` and `GraphConfigError`. The TOML must match Section 3.

Tests must assert file load, env override and `sources`, collision warning with
both values/winner, missing DSN and graph failures, expected AGE versus SQLite
failure, development-only `CI_ALLOW_SQLITE_FALLBACK=1`, derived authorization,
domain mismatch, package-relative search independent of CWD, all-domain load,
and redaction.

Validation and rollback:

```powershell
Set-Location C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
python -m pytest tests/test_graph_config.py -v
python -c "from copilot_sdk.config import GraphConfig; print(GraphConfig.load('trading'))"
```

Rollback deletes only the new files. Gate: tests pass, all domains load, and no
secret appears in diagnostics.

### Step 2: Trading

Modify `copilot-sdk/apps/trading/backend/app/graph_status.py` and its existing
tests. Import `GraphConfig`; replace the seven direct environment reads in
`TradingActiveGraphConfig.from_env` with `GraphConfig.load("trading")` and map
typed fields. Preserve validation, status shape, factory delegation, and TRD-
ID generation. Tests assert prefix, wrong graph/domain rejection, derived
authorization, missing DSN, and the expected-backend SQLite guard.

```powershell
Set-Location C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
python -m pytest apps/trading/backend/tests/ -q --timeout=120
```

Rollback is reader-only. Gate: full Trading suite passes and explicit AGE
cannot silently resolve SQLite.

### Step 3: Purchasing and DataOps

Modify `copilot-sdk/apps/purchasing/backend/app/graph_status.py`,
`copilot-sdk/apps/dataops/backend/app/graph_status.py`, and their graph-status
tests. Replace each `from_env` getenv block with
`GraphConfig.load("purchasing")`/`GraphConfig.load("dataops")`; preserve
DataOps live-age semantics, status response keys, factory args, and PUR-/DOPS-
ID generation. Add the same guard, domain, graph, authorization, and prefix
tests.

```powershell
Set-Location C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120
python -m pytest apps/dataops/backend/tests/ -q --timeout=120
```

Rollback either reader independently. Gate: both suites pass.

### Step 4: S2P

Modify `s2p-copilot/backend/app/s2p_graph_status.py`, its config tests, and
the three S2P live-test helpers. Import the installed SDK loader and call
`GraphConfig.load("s2p")`; retain explicit environment mapping for unit tests.
Implement `is_live_age_configured(domain)` while preserving active, parallel,
and shadow opt-in behavior. Verify the SDK package is importable from S2P's
CWD.

```powershell
Set-Location C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend
python -m pytest tests/ -q --timeout=120
```

Rollback S2P reader/helper changes. Gate: full S2P suite passes.

### Step 5: SOC

SOC domain-scoping v1.2 owns `soc_decision_where()` and must run first (that
work is already complete). Then modify only the AGE branch of
`gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py` to import `GraphConfig` and
use typed DSN/graph/backend values. Do not touch the helper or predicates.
Preserve Neo4j fallback. Add SOC config tests for missing DSN, graph selection,
and unchanged domain-scoped reads.

```powershell
Set-Location C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend
python -m pytest tests/ -q --timeout=300
```

Rollback the AGE-branch import only. Gate: SOC suite passes and helper diff is
empty.

### Step 6: demo.py

Modify `copilot-sdk/demo.py` and launcher tests. Import the loader, translate
typed values into legacy child environment names, and use `setdefault` for
defaults. Keep `demo.py` as the sole sanctioned env-writer; scope
`DEMO_NO_RESEED`, frontend variables, and `SOC_LEARNING_ENABLED` to children.

```powershell
Set-Location C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
python demo.py --help
python demo.py --status
```

Rollback COPILOTS translation. Gate: parent environment unchanged and explicit
AGE values survive launch.

### Step 7: phase scripts

Modify `copilot-sdk/scripts/phase_config.py`, consumers, and add
`copilot-sdk/tests/test_phase_config.py`. Call `GraphConfig.load(domain)` for
graph fields; retain phase-only paths, payloads, endpoints, checkpoints, and
outbox paths. Add `--print-config` with source display and redaction.

```powershell
Set-Location C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
python scripts/phase_config.py --domain trading
python scripts/phase_config.py --domain s2p
python -m pytest tests/test_phase_config.py -v
```

Rollback phase_config only. Gate: all domains resolve the previous paths and
prefixes.

### Step 8: harden

Add CI config-load coverage and release notes. Load all five domains in
production profile, reject TOML authorization keys, and assert every AGE
declaration has DSN/graph. After two releases remove direct env fallbacks;
the loader's env override API remains. `CI_ALLOW_SQLITE_FALLBACK=1` stays
development-only.

```powershell
Set-Location C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
python -m pytest tests/ -q --timeout=600
python -c "from copilot_sdk.config import GraphConfig; [GraphConfig.load(d) for d in ('soc','trading','purchasing','dataops','s2p')]; print('all domains valid')"
```

Rollback by re-enabling compatibility fallbacks for one release. Final gate:
no silent fallback and all domains validate.

## 7. Risks and controls

Env/file drift logs both redacted values and the env winner. Authorization
tampering is prevented by derivation. Empty AGE DSNs fail at load. Package
relative search prevents CWD drift. Python 3.11 is the floor with a guarded
tomli fallback. SOC sequencing prevents conflict with domain-scoping v1.2.
Destructive AGE remains environment-only.

## 8. Reading log

Source ranges read for this contract include v1 (`copilot-sdk/docs/design/graph_config_consolidation_v1.md:1-436`),
the four graph-status modules, SOC `neo4j.py` and `main.py`, `demo.py`,
`scripts/phase_config.py`, all S2P/ci-platform/SOC test gates cited in Section 2, and
Python-version declarations at `copilot-sdk/pyproject.toml:1-30`,
`ci-platform/pyproject.toml:1-30`, and `s2p-copilot/pyproject.toml:1-20`.
