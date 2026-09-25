"""B1 delayed entrants: preregistered before execution, random_state=42.

DECISION RULE: if replay OR migration attains parity in <50 post-entry live
decisions, the measured advantage is deployment-specific accumulated value plus
switching cost, not un-copyable. If both take >50, quantify the durable lead;
exactly 50 is a boundary result. Unreached parity is right-censored at 1000-D.
Switching cost itself is not measured by this mechanism experiment.

EXPECTED RANGES supplied by the request: SOC incumbent final routing .59-.63;
DataOps .60-.65; delayed cold start initially lower, then converging. Source
audit BEFORE execution: KE-1's saved SOC endpoint is actually .81 (DataOps .63).
Both references are retained; none is a tuning target or a hard acceptance gate.

METRICS: routing_quality = informative reads / total actual reads;
action_accuracy = predicted final action == verified action, averaged over cases.
Verification here is KE-1's geometry-derived synthetic oracle, not live outcomes.

DESIGN: SOC/DataOps x D100/D250 x four arms; 1000 stream decisions, B=2,
checkpoints every 25 including N=0 and the entry instant N=D. Incumbent completes
decisions 1..D before replay/migration; entrants then process D+1 onward. Cold
start is frozen before D. Replay independently reroutes archived surface inputs
and verified evidence, NEVER reads incumbent K. Its archive contains only values
and informative flags on dimensions actually read in that historical decision,
plus its verified final-action target. No unobserved counterfactual evidence is
supplied to replay. Migration copies SQLite K weights/counters and deep-copies mu.
All arms continue independent updates on the identical future alert stream.

Reuse load_export, make_case, run_investigation, reward_learning_store and
KUtilityStore from scripts.k_learning_curve_cross_copilot. NO rewritten K update.
As in KE-1, mu and sigma are FIXED; copying mu is intentionally a no-op in value.
Replay from identical initialization and exact ordered historical evidence should
reconstruct the incumbent in this deterministic mechanism. This is a portability
control, not evidence about incomplete logs, different engines or customer cost.

PRIMARY PARITY: first checkpoint at/after entry where BOTH metrics are no more
than 1pp below the incumbent at that SAME checkpoint (outperformance qualifies).
Report routing-only, action-only, and sustained joint parity separately. Primary
decisions_to_parity is elapsed LIVE decisions since entry, not global N. At-entry
parity is zero. Sustained parity requires all remaining checkpoints through N1000;
report any subsequent losses of first parity. No unseen future checkpoints inferred.
Resolution 25 decisions; tolerance 1pp; no outcome-dependent parameter choices.

EVALUATION: 1000 independently generated, fixed held-out cases per copilot, paired
across all arms, delays and checkpoints; frozen evaluation, no labels fed back.
This differs from KE-1's fresh 50 cases/checkpoint. One training seed, no confidence
or population generalization claim. Training RNG=42; independent eval RNG=100042.
Exact-state evaluation caching only; independent state trajectories still execute.

WALL CLOCK: elapsed live decisions / verified-per-week, SOC=1200, DataOps=106.
These MAP-v20 rates are ILLUSTRATIVE assumptions; all mechanism results have tier
REAL_COMPONENT. Replay additionally costs D archived updates, reported separately;
zero weeks to parity does not mean zero compute, migration or engineering cost.

DETERMINISM: compute ALL 16 curves twice independently; compare canonical output
bytes. No timestamps, latency measurements, temp paths, SQLite file paths or
process-dependent Python hashes in JSON. Hash excludes only its own JSON field.

Run mypy before execution:
  python -m mypy experiments/vld/vld_delayed_entrant_v1.py --config-file pyproject.toml
Run:
  python -B experiments/vld/vld_delayed_entrant_v1.py
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, TypeAlias, cast

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from numpy.typing import NDArray
from scripts import k_learning_curve_cross_copilot as harness

SEED = 42
HORIZON = 1000
INTERVAL = 25
EVAL_N = 1000
BUDGET = 2
TOLERANCE = .01
TIER = 'REAL_COMPONENT'
RATES = {'soc': 1200, 'dataops': 106}
ARMS = ('arm1_incumbent', 'arm2_cold_start', 'arm3_replay', 'arm4_migration')
OUTPUT = ROOT / 'experiments/vld/results/delayed_entrant_catchup.json'
Array: TypeAlias = NDArray[np.float64]
Record: TypeAlias = dict[str, Any]


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8')


def hash_value(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass
class Learner:
    categories: list[str]
    factors: list[str]
    mu: dict[str, Array]
    sigma: Array
    tau: float
    store: Any
    sources: dict[int, str]
    updates: int = 0

    def weights(self) -> dict[str, list[float]]:
        return {c: [float(x) for x in self.store.get_weights(c)] for c in self.categories}

    def records(self) -> list[list[Any]]:
        return [list(r) for r in self.store.conn.execute(
            'SELECT category,dimension,weight,n_updates FROM k_utility ORDER BY category,dimension').fetchall()]

    def state(self) -> Record:
        return {'K': self.weights(), 'K_records': self.records(),
                'mu': {c: self.mu[c].tolist() for c in self.categories},
                'sigma': self.sigma.tolist(), 'tau': self.tau}

    def investigator(self, category: str) -> Any:
        return harness.VLDInvestigator(self.mu[category], self.sigma, self.factors, tau=self.tau)

    def learn(self, case: Record) -> Record:
        category = str(case['category'])
        investigator = self.investigator(category)
        run = cast(Record, harness.run_investigation(case, investigator, self.store.get_weights(category), budget=BUDGET))
        harness.reward_learning_store(self.store, category, self.factors, self.sources,
                                      investigator, run, set(case['informative']))
        self.updates += 1
        return run


def new_learner(copilot: str, info: Record) -> Learner:
    factors = [str(f) for f in info['factor_names']]
    categories = [str(c) for c in info['category_names']]
    return Learner(categories, factors,
                   {c: np.asarray(info['all_category_mu'][c], dtype=np.float64).copy() for c in categories},
                   np.asarray(info['sigma'], dtype=np.float64).copy(), float(info['tau']),
                   harness.KUtilityStore(harness.SQLiteDecisionStore(), d=len(factors)),
                   {int(k): str(v) for k,v in harness.DIMENSION_SOURCES[copilot].items()})


def generate_cases(learner: Learner, count: int, seed: int) -> list[Record]:
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        category = rng.choice(learner.categories)
        cases.append(cast(Record, harness.make_case(rng, category, learner.mu[category], learner.investigator(category))))
    return cases


def serial_case(case: Record) -> Record:
    return {'category': case['category'], 'surface': np.asarray(case['surface']).tolist(),
            'full': np.asarray(case['full']).tolist(), 'correct_action': int(case['correct_action']),
            'surface_action': int(case['surface_action']), 'informative': sorted(int(i) for i in case['informative'])}


def archive_decision(case: Record, run: Record) -> Record:
    selected = [int(i) for i in run['selected']]
    # Preserve only the evidence the incumbent actually acquired, not its K,
    # probabilities, Q values or unobserved coordinates of the latent full vector.
    observed = np.asarray(case['surface'], dtype=np.float64).copy()
    for dimension, _before, after in run['step_records']:
        observed[int(dimension)] = float(after[int(dimension)])
    return {'category': case['category'], 'surface': np.asarray(case['surface']).copy(),
            'full': observed, 'correct_action': int(case['correct_action']),
            'surface_action': int(case['surface_action']),
            'informative': set(case['informative']).intersection(selected),
            'available_dimensions': selected}


def migrate(source: Learner, target: Learner) -> None:
    assert target.updates == 0 and target.records() == []
    source.store.conn.backup(target.store.conn)
    target.mu = {c: source.mu[c].copy() for c in source.categories}
    target.sigma = source.sigma.copy()
    target.tau = source.tau
    assert target.store.conn is not source.store.conn
    assert all(not np.shares_memory(source.mu[c], target.mu[c]) for c in source.categories)
    assert source.state() == target.state()


def evaluate(learner: Learner, cases: list[Record]) -> Record:
    before = learner.state()
    weights = {c: learner.store.get_weights(c).copy() for c in learner.categories}
    counts = {'total_reads': 0, 'informative_reads': 0, 'correct_actions': 0, 'saves': 0, 'hurts': 0}
    decisions = []
    for case in cases:
        category = str(case['category'])
        run = harness.run_investigation(case, learner.investigator(category), weights[category], budget=BUDGET)
        for dest, src in [('total_reads','total_reads'), ('informative_reads','informative_reads'),
                          ('correct_actions','correct'), ('saves','saved'), ('hurts','hurt')]:
            counts[dest] += int(run[src])
        decisions.append([int(run['final_action']), [int(i) for i in run['selected']]])
    assert counts['total_reads'] > 0 and learner.state() == before
    return {**counts, 'tier': TIER, 'n_evaluated': len(cases),
            'routing_quality': counts['informative_reads']/counts['total_reads'],
            'action_accuracy': counts['correct_actions']/len(cases),
            'prediction_and_read_hash': hash_value(decisions)}


def qualifies(point: Record, reference: Record, metrics: tuple[str, ...]) -> bool:
    return all(float(point[m]) >= float(reference[m])-TOLERANCE-1e-12 for m in metrics)


def parity_summary(checkpoints: list[Record], incumbent: list[Record], delay: int, rate: int) -> Record:
    pairs = [(p,r) for p,r in zip(checkpoints,incumbent) if int(p['decision_count']) >= delay]
    result: Record = {}
    for label, metrics in [('joint',('routing_quality','action_accuracy')),
                           ('routing',('routing_quality',)), ('action',('action_accuracy',))]:
        good = [qualifies(p,r,metrics) for p,r in pairs]
        first = next((i for i,ok in enumerate(good) if ok), None)
        sustained = next((i for i in range(len(good)) if all(good[i:])), None)
        elapsed = None if first is None else int(pairs[first][0]['decision_count'])-delay
        stable = None if sustained is None else int(pairs[sustained][0]['decision_count'])-delay
        result[f'{label}_decisions_to_parity'] = elapsed
        result[f'{label}_sustained_decisions_to_parity'] = stable
        result[f'{label}_parity_lost_after_first'] = False if first is None else not all(good[first:])
    result['decisions_to_parity'] = result['joint_decisions_to_parity']
    elapsed = result['decisions_to_parity']
    result['wall_clock_weeks'] = None if elapsed is None else elapsed/rate
    result['wall_clock_to_parity'] = result['wall_clock_weeks']
    result['parity_global_decision'] = None if elapsed is None else delay+elapsed
    result['right_censored'] = elapsed is None
    result['observed_post_entry_decisions'] = HORIZON-delay
    result['wall_clock_conversion_status'] = 'ILLUSTRATIVE verified-throughput assumption; no measured implementation latency'
    return result


def run_delay(copilot: str, info: Record, delay: int, train: list[Record], evaluation: list[Record],
              cache: dict[str, Record]) -> dict[str, Record]:
    learners = {name: new_learner(copilot,info) for name in ARMS}
    curves: dict[str, list[Record]] = {name: [] for name in ARMS}
    incumbent = learners[ARMS[0]]
    history: list[Record] = []
    launched = False
    entry_audit: Record = {}
    try:
        for decision in range(HORIZON+1):
            if decision > 0:
                case = train[decision-1]
                run = incumbent.learn(case)
                history.append(archive_decision(case,run))
                if decision > delay:
                    for name in ARMS[1:]:
                        learners[name].learn(case)
            if decision == delay:
                replay = learners[ARMS[2]]
                assert replay.updates == 0 and replay.records() == []
                for archived in history:
                    run = replay.learn(archived)
                    assert [int(i) for i in run['selected']] == archived['available_dimensions'], 'Replay requested unarchived evidence'
                # Equality is checked AFTER learning, never used to set replay state.
                assert replay.state() == incumbent.state(), 'Historical replay failed to reconstruct state'
                migrate(incumbent, learners[ARMS[3]])
                launched = True
                entry_audit = {'tier': TIER, 'global_decision': decision,
                               'incumbent_state_hash': hash_value(incumbent.state()),
                               'cold_state_hash': hash_value(learners[ARMS[1]].state()),
                               'replay_state_hash': hash_value(replay.state()),
                               'migration_state_hash': hash_value(learners[ARMS[3]].state()),
                               'replayed_decisions': len(history),
                               'replayed_reads': sum(len(c['available_dimensions']) for c in history),
                               'replay_archive_sha256': hash_value([serial_case(c) for c in history]),
                               'replay_no_K_access': True, 'migration_independent_storage': True,
                               'mu_changes_during_training': False}
            if launched:
                for name in ARMS[2:]:
                    assert learners[name].state() == incumbent.state(), f'{name} diverged after entry'
            if decision % INTERVAL == 0:
                for name, learner in learners.items():
                    state = learner.state()
                    key = hash_value(state)
                    if key not in cache:
                        cache[key] = evaluate(learner,evaluation)
                    stats = cache[key]
                    curves[name].append({**stats, 'decision_count': decision,
                        'live_decisions': decision if name==ARMS[0] else max(0,decision-delay),
                        'phase': 'incumbent' if name==ARMS[0] else 'live' if launched else 'pre_entry',
                        'training_decisions_applied_locally': learner.updates,
                        'state_hash': key, 'k_weights_by_category': state['K'],
                        'mu_hash': hash_value(state['mu'])})
        output: dict[str, Record] = {}
        for name, learner in learners.items():
            points = curves[name]
            primary_delay = 0 if name==ARMS[0] else delay
            output[name] = {'tier': TIER, 'checkpoints': points,
                'final_routing': points[-1]['routing_quality'], 'final_action': points[-1]['action_accuracy'],
                'final_routing_quality': points[-1]['routing_quality'], 'final_action_accuracy': points[-1]['action_accuracy'],
                'final_state': learner.state(), 'budget': BUDGET,
                'entry_decision': primary_delay, 'offline_replayed_decisions': delay if name==ARMS[2] else 0,
                'initial_migrated_training_decisions': delay if name==ARMS[3] else 0,
                'verified_per_week': RATES[copilot],
                **parity_summary(points,curves[ARMS[0]],primary_delay,RATES[copilot])}
            if name in ARMS[2:]:
                output[name]['entry_state_audit'] = entry_audit
                output[name]['identical_to_incumbent_at_all_live_checkpoints'] = all(
                    p['state_hash']==r['state_hash'] and p['prediction_and_read_hash']==r['prediction_and_read_hash']
                    for p,r in zip(points,curves[ARMS[0]]) if p['decision_count']>=delay)
        return output
    finally:
        for learner in learners.values():
            learner.store.conn.close()


def compute_all(verbose: bool = True) -> Record:
    export = cast(Record,harness.load_export())
    result: Record = {}
    for copilot in ['soc','dataops']:
        generator = new_learner(copilot,cast(Record,export[copilot]))
        try:
            train = generate_cases(generator,HORIZON,SEED)
            evaluation = generate_cases(generator,EVAL_N,SEED+100000)
        finally:
            generator.store.conn.close()
        cache: dict[str,Record] = {}
        result[copilot] = {}
        for delay in [100,250]:
            if verbose: print(f'Computing {copilot} D{delay}: four curves...',flush=True)
            result[copilot][f'D{delay}'] = run_delay(copilot,cast(Record,export[copilot]),delay,train,evaluation,cache)
        assert result[copilot]['D100'][ARMS[0]] == result[copilot]['D250'][ARMS[0]], 'Delay changed incumbent'
        result[copilot]['stream_provenance'] = {'tier': TIER, 'train_seed': SEED, 'evaluation_seed': SEED+100000,
            'train_sha256': hash_value([serial_case(c) for c in train]),
            'evaluation_sha256': hash_value([serial_case(c) for c in evaluation]),
            'geometry_hash': str(harness.geometry_hash(export[copilot])),
            'training_count': HORIZON, 'evaluation_count': EVAL_N,
            'cached_unique_evaluations': len(cache)}
    return result


def attach_metadata(result: Record, sources: dict[str,str]) -> None:
    refs = cast(Record,json.loads((ROOT/'experiments/vld/k_learning_curve_cross_copilot_summary.json').read_text(encoding='utf-8')))
    expected = {'soc':[.59,.63], 'dataops':[.60,.65]}
    comparisons = {}
    verdicts = {}
    for copilot in ['soc','dataops']:
        value = float(result[copilot]['D100'][ARMS[0]]['final_routing'])
        banked = next(c for c in refs['copilots'] if c['name']==copilot)
        comparisons[copilot] = {'tier': TIER, 'preregistered_range': expected[copilot],
            'observed_incumbent_final_routing': value,
            'within_requested_range': expected[copilot][0] <= value <= expected[copilot][1],
            'KE1_banked_N500_routing': banked['final_routing_learning'],
            'comparison_limit': 'different seed, N1000 horizon and fixed 1000-case evaluation; no exact KE-1 replication claim'}
        for delay in ['D100','D250']:
            arms = result[copilot][delay]
            elapsed = [arms[name]['decisions_to_parity'] for name in ARMS[2:]]
            if any(n is not None and n < 50 for n in elapsed):
                verdict = 'deployment-specific accumulated value plus switching cost; not un-copyable under complete replay or authorized migration'
            elif any(n == 50 for n in elapsed):
                verdict = 'boundary at 50 decisions; preregistered <50 / >50 rule inconclusive'
            else:
                verdict = 'lead persists beyond 50 decisions under both replay and migration; report censoring and exact parity delays'
            verdicts[f'{copilot}/{delay}'] = {'tier': TIER, 'verdict': verdict,
                                           'replay_decisions': elapsed[0], 'migration_decisions': elapsed[1]}
    result['metadata'] = {
        'experiment_id': 'B1-delayed-entrant-v1', 'random_state': SEED, 'tier': TIER,
        'harness_source': 'scripts/k_learning_curve_cross_copilot.py',
        'reused_functions': ['load_export','make_case','run_investigation','reward_learning_store','KUtilityStore'],
        'source_sha256': sources, 'n_curves': 16, 'horizon': HORIZON, 'checkpoint_interval': INTERVAL,
        'evaluation_cases_per_checkpoint': EVAL_N, 'budget': BUDGET,
        'metric_definitions': {'routing_quality':'informative reads / total actual reads',
            'action_accuracy':'count(predicted final action == verified action) / evaluated cases'},
        'verification_source': 'KE-1 synthetic full-vector geometry oracle with informative-read tags',
        'primary_parity': 'both metrics >= contemporaneous incumbent minus .01; first checkpoint at/after D; elapsed decisions since D',
        'sustained_parity': 'first checkpoint satisfying parity at every remaining observed checkpoint; finite horizon only',
        'mu_and_sigma_updates': False, 'state_migration': 'deep-copy mu and sigma plus SQLite K weights/update counters; no shared arrays or connection',
        'replay_contract': 'independent routing from archived surface, acquired evidence, and verified action/informative tags; no K; no unobserved evidence',
        'wall_clock_rates_per_week': RATES,
        'wall_clock_rate_source': 'docs/design/map_vld_addendum_v20 (1).md: verified-outcome latency table',
        'wall_clock_rate_status': 'ILLUSTRATIVE reference-firm assumptions; experiment evidence tier remains REAL_COMPONENT',
        'wall_clock_excludes': ['offline replay compute','migration engineering','archive preparation','new verification latency beyond assumed throughput'],
        'parity_tolerance': TOLERANCE, 'expected_range_comparison': comparisons, 'preregistered_verdicts': verdicts,
        'limitations': ['single training seed and fixed synthetic held-out cohort; no confidence intervals',
                       'stationary shared stream, identical algorithm and starting geometry',
                       'K-only KE-1 learning; learned mu migration not independently tested',
                       'identical deterministic replay/migration is an expected control, not a switching-cost measurement',
                       'first-parity crossing may be transient; sustained parity and later losses also reported'],
        'determinism_self_test': {'passed': True, 'independent_full_computations': 2},
        'determinism_hash_scope': 'SHA256 of canonical sorted-key indented UTF-8 JSON with trailing LF, excluding only metadata.determinism_hash',
    }


def main() -> None:
    protected = [Path(__file__),ROOT/'scripts/k_learning_curve_cross_copilot.py',ROOT/'scripts/k_learning_curve_experiment.py',
                 ROOT/'real_centroids_v1.json',ROOT/'copilot_sdk/scoring/scorer.py',
                 ROOT/'copilot_sdk/scoring/investigation.py',ROOT/'copilot_sdk/backend/investigation_router.py',
                 ROOT/'experiments/vld/k_learning_curve_cross_copilot_summary.json',
                 ROOT/'experiments/vld/results/result_manifest.csv',ROOT/'experiments/vld/results/result_manifest_README.md',
                 ROOT/'docs/design/map_vld_addendum_v20 (1).md']
    before = {p.relative_to(ROOT).as_posix():file_hash(p) for p in protected}
    print('B1 preregistration active; full computation 1/2.',flush=True)
    first = compute_all()
    attach_metadata(first,before)
    print('Determinism self-test: independent full computation 2/2.',flush=True)
    second = compute_all()
    attach_metadata(second,before)
    assert canonical(first)==canonical(second), 'Determinism self-test failed'
    assert before=={p.relative_to(ROOT).as_posix():file_hash(p) for p in protected}, 'Protected source changed'
    first['metadata']['determinism_hash'] = hash_value(first)
    blob = canonical(first)
    if OUTPUT.exists():
        existing = cast(Record,json.loads(OUTPUT.read_text(encoding='utf-8')))
        if existing.get('metadata',{}).get('source_sha256')==before:
            assert OUTPUT.read_bytes()==blob, 'Existing same-protocol output differs'
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_bytes(blob)
    for copilot in ['soc','dataops']:
        for delay in ['D100','D250']:
            for name in ARMS:
                r = first[copilot][delay][name]
                print(f"{copilot:7s} {delay} {name:18s} routing={r['final_routing']:.4f} action={r['final_action']:.4f} "
                      f"parity={r['decisions_to_parity']} sustained={r['joint_sustained_decisions_to_parity']} weeks={r['wall_clock_weeks']}")
    print('Determinism self-test PASSED; payload SHA256:',first['metadata']['determinism_hash'])
    print('Output file SHA256:',hashlib.sha256(blob).hexdigest())
    print('Wrote',OUTPUT)


if __name__=='__main__':
    main()
