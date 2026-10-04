"""CPU-only scenario-specialization diagnostic; never opens final test files.

This does not alter the active evaluator, optimizer, selected source, or protocol.
Run as a single low-priority process with ``nice -n 10 python -m ...``.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import time

import numpy as np
from numba import njit

from .evaluator import prelude
from .perishable import evaluate, inventory_cap, sample_demands, scenarios


def specialize_validated_source(source, scenario):
    """Bind scenario inputs at function entry; preserve subsequent assignments."""
    tree = ast.parse(source)
    fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef))
    values = dict(mu=float(scenario.mean), cv=float(scenario.sd / scenario.mean),
                  f=float(scenario.f), L=int(scenario.L))
    assert tuple(a.arg for a in fn.args.args) == (
        'age', 'pipeline', 'mu', 'cv', 'f', 'L', '_opt_values')
    fn.args.args = [a for a in fn.args.args if a.arg not in values]
    injected = [ast.Assign(targets=[ast.Name(id=k, ctx=ast.Store())],
                           value=ast.Constant(v)) for k, v in values.items()]
    # Inserting assignments rather than replacing name loads preserves local
    # reassignment. Existing policy statements and arithmetic order stay intact.
    fn.body = injected + fn.body
    return ast.unparse(ast.fix_missing_locations(tree))


def compile_policy(source, specialized=False):
    ns = {}
    exec(compile(source, '<validated-specialization-diagnostic>', 'exec'), ns)
    numeric = njit(ns['compute_order_amount'], boundscheck=True)
    if specialized:
        @njit
        def wrapper(age, pipeline, theta, mu, cv, f, L):
            return numeric(age, pipeline, theta)
    else:
        @njit
        def wrapper(age, pipeline, theta, mu, cv, f, L):
            return numeric(age, pipeline, mu, cv, f, L, theta)
    return wrapper


def main():
    started = time.monotonic()
    run = Path('output/overnight_search/20260917')
    destination = run / 'diagnostics' / 'specialization'
    destination.mkdir(parents=True, exist_ok=True)
    # Use exactly the current evaluator's prepared validator, including its
    # local-array mutation allowance and import normalization, without executing
    # its unrelated simulator or job body.
    validator = prelude().split('\nfrom dataclasses import asdict, dataclass')[0]
    namespace = {'__name__': '_specialization_validator'}
    exec(validator, namespace)
    prepare = namespace['prepare_policy']
    chosen = [s for s in scenarios()
              if (s.m, s.cv) in ((3, 1.5), (5, 2.0))]
    rng = np.random.default_rng(98712011)
    report = {'scope': 'synthetic diagnostic paths; no final test access',
              'seed': 98712011, 'paths': 8, 'periods': 250, 'burnin': 50,
              'records': [], 'active_evaluator_modified': False}
    for label in ('evolution_r2', 'evolution_r3'):
        selected = json.loads((run / 'selected' / (label + '.json')).read_text())['selected']
        prepared = prepare(selected['code'], None)
        original = compile_policy(prepared['source'])
        bounds = np.array([[p['min'], p['max']] for p in prepared['opt_params'].values()])
        for s in chosen:
            if time.monotonic() - started > 270:
                report['time_bound_reached'] = True
                break
            transformed = specialize_validated_source(prepared['source'], s)
            specialized = compile_policy(transformed, True)
            (destination / (label + '_' + s.name + '.py')).write_text(transformed)
            theta_values = [np.asarray(prepared['values']),
                            np.asarray(selected['train_theta'][s.name])]
            theta_values += [rng.uniform(bounds[:, 0], bounds[:, 1]) for _ in range(3)]
            cap = inventory_cap(s)
            states = [rng.multinomial(int(rng.integers(cap + 1)),
                                     np.ones(s.m + s.L - 1) / (s.m + s.L - 1))
                      for _ in range(120)]
            states += [np.zeros(s.m + s.L - 1, dtype=np.int64)]
            largest = 0.0
            raw_exact = True
            projected_exact = True
            compile_start = time.monotonic()
            original(states[0][:s.m], states[0][s.m:], theta_values[0],
                     s.mean, s.sd / s.mean, s.f, s.L)
            specialized(states[0][:s.m], states[0][s.m:], theta_values[0],
                        s.mean, s.sd / s.mean, s.f, s.L)
            compile_seconds = time.monotonic() - compile_start
            for theta in theta_values:
                for state in states:
                    args = (state[:s.m].copy(), state[s.m:].copy(), theta,
                            s.mean, s.sd / s.mean, s.f, s.L)
                    a, b = original(*args), specialized(*args)
                    largest = max(largest, abs(a - b))
                    raw_exact &= a == b
                    remaining = max(0, cap - state.sum())
                    projected_exact &= np.rint(np.clip(a, 0, remaining)) == np.rint(np.clip(b, 0, remaining))
            tape = sample_demands(s, 8, 250, 98712011)
            path_exact = True
            metric_exact = True
            # Warm the objective compilation before timings.
            for theta in theta_values:
                a = evaluate(s, tape, original, theta, 50)
                b = evaluate(s, tape, specialized, theta, 50)
                path_exact &= np.array_equal(a[0], b[0])
                metric_exact &= np.array_equal(a[1], b[1])
            timings = {'original': [], 'specialized': []}
            cpu_timings = {'original': [], 'specialized': []}
            for repeat in range(5):
                pairs = [('original', original), ('specialized', specialized)]
                if repeat % 2:
                    pairs.reverse()
                for name, callback in pairs:
                    t = time.monotonic()
                    cpu_t = time.process_time()
                    evaluate(s, tape, callback, theta_values[1], 50)
                    cpu_timings[name].append(time.process_time() - cpu_t)
                    timings[name].append(time.monotonic() - t)
            record = dict(method=label, origin=selected['origin'], scenario=s.name,
                          raw_action_exact=bool(raw_exact), max_raw_action_error=largest,
                          projected_action_exact=bool(projected_exact),
                          path_cost_exact=bool(path_exact), metric_exact=bool(metric_exact),
                          state_theta_checks=len(states) * len(theta_values),
                          path_theta_checks=8 * len(theta_values),
                          policy_compile_seconds=compile_seconds,
                          median_original_seconds=float(np.median(timings['original'])),
                          median_specialized_seconds=float(np.median(timings['specialized'])),
                          speedup=float(np.median(timings['original']) / np.median(timings['specialized'])),
                          median_original_cpu_seconds=float(np.median(cpu_timings['original'])),
                          median_specialized_cpu_seconds=float(np.median(cpu_timings['specialized'])),
                          cpu_speedup=float(np.median(cpu_timings['original']) / np.median(cpu_timings['specialized'])))
            report['records'].append(record)
            report['wall_seconds'] = time.monotonic() - started
            (destination / 'result.json').write_text(json.dumps(report, indent=2))
            print(json.dumps(record), flush=True)
    report['wall_seconds'] = time.monotonic() - started
    (destination / 'result.json').write_text(json.dumps(report, indent=2))
    print('RESULT=' + str(destination / 'result.json'), flush=True)


if __name__ == '__main__':
    main()
