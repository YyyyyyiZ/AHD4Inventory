"""Bounded, exact per-objective action memoization diagnostic only.

No active evaluator changes, API calls, or final-test reads. Cache storage is at
most 4 MiB of NumPy buffers and is recreated for every theta/scenario objective.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import resource
import time

import numpy as np
from numba import njit

from .evaluator import prelude
from .optimization import optimize
from .perishable import evaluate, inventory_cap, sample_demands, scenarios, transition_inplace
from .specialization_diagnostic import compile_policy


@njit
def memoized_kernel(policy, theta, demands, m, L, cap, mu, cv, f, h, p, w,
                    burnin, dense, slots, slot_bits, max_entries, audit):
    npaths, periods, _ = demands.shape
    if not 0 <= burnin < periods:
        raise ValueError('Invalid burnin')
    values = np.full(slots, np.nan)
    keys = np.full(0 if dense else slots, -1, dtype=np.int64)
    entries = 0
    hits = 0
    misses = 0
    costs = np.zeros(npaths)
    components = np.zeros((npaths, 3))
    for path in range(npaths):
        age = np.zeros(m, dtype=np.int64)
        pipeline = np.zeros(max(0, L - 1), dtype=np.int64)
        for t in range(periods):
            key = 0
            multiplier = 1
            for j in range(m):
                key += age[j] * multiplier
                multiplier *= cap + 1
            for j in range(len(pipeline)):
                key += pipeline[j] * multiplier
                multiplier *= cap + 1
            if dense:
                slot = key
                found = not np.isnan(values[slot])
            else:
                slot = np.int64((np.uint64(key) * np.uint64(11400714819323198485))
                                >> np.uint64(64 - slot_bits))
                while keys[slot] != -1 and keys[slot] != key:
                    slot = (slot + 1) & (slots - 1)
                found = keys[slot] == key
            if found:
                raw_order = values[slot]
                hits += 1
            else:
                raw_order = policy(age.copy(), pipeline.copy(), theta, mu, cv, f, L)
                if not np.isfinite(raw_order):
                    raise ValueError('Nonfinite policy action')
                misses += 1
                if dense or entries < max_entries:
                    values[slot] = raw_order
                    if not dense:
                        keys[slot] = key
                    entries += 1
            if audit:
                check = policy(age.copy(), pipeline.copy(), theta, mu, cv, f, L)
                if raw_order != check:
                    raise ValueError('Raw action parity failed')
            # The following is copied without arithmetic changes from the
            # trusted evaluator. Cached values precede projection/rounding.
            if not np.isfinite(raw_order):
                raise ValueError('Nonfinite policy action')
            raw_order = max(0.0, raw_order)
            if cap >= 0:
                raw_order = min(raw_order, max(0, cap - age.sum() - pipeline.sum()))
            if raw_order > 1e12:
                raise ValueError('Numerically unsafe policy action')
            order = int(np.rint(raw_order))
            waste, lost, held = transition_inplace(
                age, pipeline, order, demands[path, t, 0], demands[path, t, 1], L)
            if t >= burnin:
                costs[path] += w * waste + p * lost + h * held
                components[path, 0] += waste
                components[path, 1] += lost
                components[path, 2] += order
    return costs / (periods - burnin), components / (periods - burnin), hits, misses, entries


def cache_configuration(s, periods, paths, max_entries=100_000):
    cap = inventory_cap(s)
    dimensions = s.m + max(0, s.L - 1)
    key_count = (cap + 1) ** dimensions
    if cap < 0 or key_count > np.iinfo(np.int64).max:
        raise ValueError('Finite cap and signed-int64 collision-free key required')
    if max_entries < 1:
        raise ValueError('At least one sparse-cache entry is required')
    max_entries = min(int(max_entries), 100_000, paths * periods,
                      math.comb(cap + dimensions, dimensions))
    dense = key_count <= 524_288
    if dense:
        return dict(dense=True, slots=key_count, slot_bits=0, max_entries=max_entries,
                    buffer_bytes=key_count * 8)
    bits = max(1, (2 * max_entries - 1).bit_length())
    return dict(dense=False, slots=1 << bits, slot_bits=bits, max_entries=max_entries,
                buffer_bytes=(1 << bits) * 16)


def cached_evaluate(s, tape, policy, theta, burnin, audit=False, max_entries=100_000):
    cfg = cache_configuration(s, tape.shape[1], tape.shape[0], max_entries)
    return memoized_kernel(policy, np.asarray(theta, dtype=float), tape, s.m, s.L,
                           inventory_cap(s), s.mean, s.sd / s.mean, s.f, s.h, s.p,
                           s.w, burnin, cfg['dense'], cfg['slots'], cfg['slot_bits'],
                           cfg['max_entries'], audit)


def main():
    started = time.monotonic()
    run = Path('output/overnight_search/20260917')
    destination = run / 'diagnostics' / 'memoization'
    destination.mkdir(parents=True, exist_ok=True)
    validator = prelude().split('\nfrom dataclasses import asdict, dataclass')[0]
    namespace = {'__name__': '_memoization_validator'}
    exec(validator, namespace)
    prepare = namespace['prepare_policy']
    chosen = [s for s in scenarios() if (s.m, s.cv) in ((3, 1.5), (5, 2.0))]
    rng = np.random.default_rng(98713011)
    report = {'scope': 'fresh diagnostic paths only; no final tests', 'seed': 98713011,
              'records': [], 'optimization_parity': [], 'max_cache_array_bytes': 4 * 1024 * 1024,
              'active_evaluator_modified': False}
    for label in ('evolution_r2', 'evolution_r3'):
        selected = json.loads((run / 'selected' / (label + '.json')).read_text())['selected']
        prepared = prepare(selected['code'], None)
        policy = compile_policy(prepared['source'])
        bounds = np.array([[p['min'], p['max']] for p in prepared['opt_params'].values()])
        for s in chosen:
            if time.monotonic() - started > 250:
                report['time_bound_reached'] = True
                break
            theta_values = [np.asarray(prepared['values']), np.asarray(selected['train_theta'][s.name])]
            theta_values += [rng.uniform(bounds[:, 0], bounds[:, 1]) for _ in range(3)]
            audit_tape = sample_demands(s, 8, 400, 98713011)
            for theta in theta_values:
                reference = evaluate(s, audit_tape, policy, theta, 100)
                observed = cached_evaluate(s, audit_tape, policy, theta, 100, audit=True)
                assert np.array_equal(reference[0], observed[0])
                assert np.array_equal(reference[1], observed[1])
            # Force hash saturation separately to verify exact fallback.
            saturation_verified = False
            if not cache_configuration(s, 400, 8)['dense']:
                reference = evaluate(s, audit_tape, policy, theta_values[1], 100)
                saturated = cached_evaluate(s, audit_tape, policy, theta_values[1],
                                            100, audit=True, max_entries=2)
                assert np.array_equal(reference[0], saturated[0])
                assert np.array_equal(reference[1], saturated[1])
                saturation_verified = saturated[4] == 2
            tape = sample_demands(s, 32, 1000, 98713012)
            theta = theta_values[1]
            reference = evaluate(s, tape, policy, theta, 200)
            observed = cached_evaluate(s, tape, policy, theta, 200)
            assert np.array_equal(reference[0], observed[0])
            assert np.array_equal(reference[1], observed[1])
            timings = {'original': [], 'cached': []}
            wall = {'original': [], 'cached': []}
            for repeat in range(3):
                order = ('original', 'cached') if repeat % 2 == 0 else ('cached', 'original')
                for name in order:
                    tick, cpu_tick = time.monotonic(), time.process_time()
                    if name == 'original':
                        evaluate(s, tape, policy, theta, 200)
                    else:
                        cached_evaluate(s, tape, policy, theta, 200)
                    timings[name].append(time.process_time() - cpu_tick)
                    wall[name].append(time.monotonic() - tick)
            cfg = cache_configuration(s, 1000, 32)
            record = dict(method=label, origin=selected['origin'], scenario=s.name,
                          audited_raw_actions=8 * 400 * len(theta_values),
                          path_cost_exact=True, metrics_exact=True,
                          saturation_fallback_verified=bool(saturation_verified),
                          hits=int(observed[2]), misses=int(observed[3]), entries=int(observed[4]),
                          hit_rate=float(observed[2] / (observed[2] + observed[3])),
                          cache=cfg,
                          original_cpu_seconds=float(np.median(timings['original'])),
                          cached_cpu_seconds=float(np.median(timings['cached'])),
                          cpu_speedup=float(np.median(timings['original']) / np.median(timings['cached'])),
                          wall_speedup=float(np.median(wall['original']) / np.median(wall['cached'])))
            report['records'].append(record)
            report['wall_seconds'] = time.monotonic() - started
            report['process_peak_rss_bytes_macos'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            (destination / 'result.json').write_text(json.dumps(report, indent=2))
            print(json.dumps(record), flush=True)
        # A complete optimizer run checks that objective ties, parameter choices,
        # and the entire DE trajectory remain unchanged, not just final scores.
        s = chosen[-1]
        tape = sample_demands(s, 4, 200, 98713013)
        traces = {'original': [], 'cached': []}
        def make_objective(name):
            def objective(theta):
                callback = evaluate if name == 'original' else cached_evaluate
                cost = float(callback(s, tape, policy, theta, 50)[0].mean())
                traces[name].append((np.asarray(theta).tolist(), cost))
                return cost
            return objective
        records = {name: optimize(make_objective(name), bounds, prepared['values'],
                                  budget=33, seed=98713014)
                   for name in ('original', 'cached')}
        assert traces['original'] == traces['cached']
        assert records['original']['theta'] == records['cached']['theta']
        assert records['original']['cost'] == records['cached']['cost']
        opt_record = dict(method=label, scenario=s.name, budget=33, nfev=records['original']['nfev'],
                          exact_trajectory=True, exact_theta=True, exact_cost=True)
        report['optimization_parity'].append(opt_record)
        (destination / 'result.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(opt_record), flush=True)
    report['wall_seconds'] = time.monotonic() - started
    (destination / 'result.json').write_text(json.dumps(report, indent=2))
    print('RESULT=' + str(destination / 'result.json'), flush=True)


if __name__ == '__main__':
    main()
