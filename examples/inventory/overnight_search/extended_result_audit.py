"""Finite metadata-only audit of sealed extended results; never scores policies."""
from __future__ import annotations

import argparse
import ast
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .evaluator import prelude
from .perishable import Scenario, inventory_cap


PRIMARY = Path('output/overnight_search/20260917')
RUN = PRIMARY / 'extended'
BAEK = PRIMARY / 'baek' / 'extended'
EXPECTED = {f'{a}_r{i}' for a in ('one_query', 'best_of_n', 'evolution') for i in (1, 2, 3)} | {
    f'baseline_{a}' for a in ('constant', 'base_stock', 'capped_base_stock', 'age_discount', 'bsp_low_ew_mixed_l2')}
SETTINGS = dict(paths=128, burnin=500, horizon=3000, seed=18094001)


def pending():
    missing = []
    for name in ('numeric_policies_freeze.json', 'baek_policies_freeze.json', 'numeric_evaluation_completed.json'):
        if not (RUN / name).exists():
            missing.append(name)
    for name in sorted(EXPECTED):
        for suffix in ('', '_without_tuning'):
            if not (RUN / 'test' / f'{name}{suffix}.json').exists():
                missing.append(f'test/{name}{suffix}.json')
    for repeat in (1, 2, 3):
        path = RUN / 'test' / f'baek_r{repeat}.json'
        if not path.exists():
            missing.append(str(path.relative_to(RUN)))
        else:
            try:
                row = json.loads(path.read_text())
                if not row.get('complete') or len(row.get('results', {})) != 8:
                    missing.append(str(path.relative_to(RUN)) + ':incomplete')
            except (json.JSONDecodeError, OSError):
                missing.append(str(path.relative_to(RUN)) + ':not_readable_yet')
    return missing


def audit():
    files, checks, errors, limitations = {}, [], [], []
    def read(path):
        raw = path.read_bytes()
        files[str(path.relative_to(PRIMARY))] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    def text(path):
        raw = path.read_bytes()
        files[str(path.relative_to(PRIMARY))] = hashlib.sha256(raw).hexdigest()
        return raw.decode()
    def sha(value):
        return hashlib.sha256(value.encode()).hexdigest()
    def check(label, condition):
        checks.append(label)
        if not condition:
            errors.append(label)
    freeze = read(RUN / 'numeric_policies_freeze.json')
    baek_seal = read(RUN / 'baek_policies_freeze.json')
    completed = read(RUN / 'numeric_evaluation_completed.json')
    check('exact14_artifacts', set(freeze['artifacts']) == EXPECTED)
    check('completed_settings_and_count', completed['test_settings'] == SETTINGS and completed['policy_count'] == 14)
    check('completed_split', completed['discovery_instances'] == 4 and completed['transfer_instances'] == 4)
    # Only validator definitions/imports execute; no candidate code is executed.
    namespace = {'__name__': '_extended_provenance_validator'}
    exec(prelude().split('\nfrom dataclasses import asdict, dataclass')[0], namespace)
    prepare = namespace['prepare_policy']
    specs = [Scenario(f'perish_m{m}_L2_cv{cv:g}_f{f:g}', m=m, L=2, cv=cv, f=f)
             for m in (7, 8) for cv in (1.5, 2.0) for f in (0.0, 0.5)]
    by_name = {s.name: s for s in specs}
    names = set(by_name)
    max_mean_error, max_metric_error = 0.0, 0.0
    numeric_rows, numeric_paths, baek_rows = 0, 0, 0
    numeric, selected, defaults_differ, baek = [], [], [], []
    def row_check(label, row):
        nonlocal max_mean_error, max_metric_error
        paths = np.asarray(row['path_costs'], dtype=float)
        check(label + ':128finitepaths', paths.shape == (128,) and bool(np.isfinite(paths).all()))
        error = abs(float(np.mean(paths)) - row['cost'])
        max_mean_error = max(max_mean_error, error)
        check(label + ':mean', error <= 1e-10)
        metrics = np.asarray(row['metrics'], dtype=float)
        check(label + ':finite_metrics', metrics.shape == (3,) and bool(np.isfinite(metrics).all()) and bool((metrics >= 0).all()))
        error = abs(row['cost'] - 100 * (metrics[0] + metrics[1]))
        max_metric_error = max(max_metric_error, error)
        check(label + ':cost_components', error <= 1e-9)
    for name, artifact in sorted(freeze['artifacts'].items()):
        check(name + ':freeze_codehash', sha(artifact['code']) == artifact['code_sha256'])
        check(name + ':freeze8theta', set(artifact['theta']) == names)
        prepared = prepare(artifact['code'], None)
        defaults = []
        for line in artifact['code'].splitlines():
            if 'OPT_PARAM:' in line:
                assignment = ast.parse(line.split('#', 1)[0].strip()).body[0]
                defaults.append(float(ast.literal_eval(assignment.value)))
        check(name + ':literal_defaults', defaults == prepared['values'])
        if defaults != [v['initial'] for v in prepared['opt_params'].values()]:
            defaults_differ.append(name)
        if name.startswith('baseline_'):
            source = RUN / 'baselines' / name.removeprefix('baseline_') / 'policy.py'
            check(name + ':baseline_source', text(source) == artifact['code'])
        else:
            selection = read(RUN / 'selected' / f'{name}.json')['selected']
            check(name + ':selected_code', selection['code'] == artifact['code'])
            check(name + ':selected_structure', selection['structure_sha256'] == prepared['structure_sha256'])
            origin = RUN / selection['origin'] / 'policy.py'
            if origin.exists():
                check(name + ':origin_code', text(origin) == artifact['code'])
            else:
                limitations.append(f'{name}: direct origin source file absent ({selection["origin"]}); selected/frozen code checked.')
            selected.append(dict(method=name, origin=selection['origin'], code_sha256=artifact['code_sha256'],
                                 structure_sha256=prepared['structure_sha256']))
        refit = read(RUN / 'refit' / f'{sha(artifact["code"])[:20]}.json')
        check(name + ':refit_theta', artifact['theta'] == {s: row['theta'] for s, row in refit['results'].items()})
        for raw in (False, True):
            artifact_name = name + ('_without_tuning' if raw else '')
            record = read(RUN / 'test' / f'{artifact_name}.json')
            theta = {s.name: defaults for s in specs} if raw else artifact['theta']
            request = dict(op='evaluate', code=artifact['code'], scenarios=[asdict(s) for s in specs],
                           optimizer_seed=1731, **SETTINGS, theta=theta)
            fingerprint = sha(json.dumps(request, sort_keys=True))
            check(artifact_name + ':full_request_hash', record['request_sha256'] == fingerprint)
            check(artifact_name + ':codehash', record['code_sha256'] == artifact['code_sha256'])
            check(artifact_name + ':structurehash', record['structure_sha256'] == prepared['structure_sha256'])
            check(artifact_name + ':parameter_declarations', record['parameters'] == prepared['opt_params'])
            check(artifact_name + ':normalization', record.get('import_normalization', []) == prepared.get('import_normalization', []))
            check(artifact_name + ':8scenarios', set(record['results']) == names)
            check(artifact_name + ':transitions', record['transitions'] == 8 * 128 * 3500)
            for scenario, row in record['results'].items():
                label = artifact_name + ':' + scenario
                check(label + ':theta', row['theta'] == theta[scenario])
                check(label + ':zero_test_nfev', row['nfev'] == 0)
                check(label + ':cap', row['cap'] == inventory_cap(by_name[scenario]))
                row_check(label, row)
                numeric_rows += 1
                numeric_paths += len(row['path_costs'])
            numeric.append(dict(artifact=artifact_name, request_sha256=fingerprint,
                                code_sha256=record['code_sha256'], scenarios=len(record['results']),
                                action_cache=record.get('action_cache', {}).get('enabled')))
    missing_baek = []
    for repeat in (1, 2, 3):
        source = BAEK / 'sessions' / f'l2_r{repeat}' / 'policy.py'
        code = text(source)
        code_hash = sha(code)
        check(f'baek_r{repeat}:source_seal', code_hash == baek_seal['sha256'][str(repeat)])
        session = read(source.with_name('result.json'))
        check(f'baek_r{repeat}:session_hash', session['code_sha256'] == code_hash)
        check(f'baek_r{repeat}:session_code', session['final_code'] == code)
        rows = {}
        for scenario in specs:
            path = RUN / 'baek_scores' / f'r{repeat}' / f'{scenario.name}.json'
            if not path.exists():
                missing_baek.append(str(path.relative_to(RUN)))
                continue
            row = read(path)
            rows[scenario.name] = row
            check(f'baek_r{repeat}:{scenario.name}:codehash', row['code_sha256'] == code_hash)
            check(f'baek_r{repeat}:{scenario.name}:settings', row['test_settings'] == SETTINGS)
            row_check(f'baek_r{repeat}:{scenario.name}', row)
            baek_rows += 1
        aggregate = read(RUN / 'test' / f'baek_r{repeat}.json')
        check(f'baek_r{repeat}:aggregate', aggregate['results'] == rows)
        check(f'baek_r{repeat}:complete', aggregate['complete'] and len(rows) == 8)
        if 'policy_sha256' in aggregate:
            check(f'baek_r{repeat}:aggregate_hash', aggregate['policy_sha256'] == code_hash)
        baek.append(dict(repeat=repeat, cases=len(rows), code_sha256=code_hash))
    manifest = read(BAEK / 'manifest.json')
    for filename, field in [('trusted_prelude.py', 'trusted_prelude_sha256'), ('prompt.txt', 'prompt_sha256')]:
        check('baek_manifest:' + filename, sha(text(BAEK / filename)) == manifest['identity'][field])
    return dict(audit_utc=datetime.now(timezone.utc).isoformat(), status='pass' if not errors else 'issues_found',
                settings=SETTINGS, numeric_freeze_utc=freeze['created_utc'],
                baek_freeze_utc=baek_seal.get('created_utc', baek_seal.get('utc')),
                numeric_artifacts=len(numeric), numeric_scenario_rows=numeric_rows,
                numeric_path_cost_values=numeric_paths, baek_scenario_rows=baek_rows,
                baek_missing=missing_baek, check_count=len(checks), errors=errors,
                max_mean_error=max_mean_error, max_metric_cost_error=max_metric_error,
                defaults_differ_from_declared_initial=defaults_differ, limitations=limitations,
                selected=selected, numeric=numeric, baek=baek, files_sha256=files,
                constraints=dict(policy_calls=0, demand_tapes_generated=0, paid_calls=0, strategies_modified=False))


def save(result):
    destination = RUN / 'diagnostics' / 'extended_result_audit'
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    lines = ['# Extended final-result provenance audit', '',
             f"Audit time: **{result['audit_utc']}**. Scope: existing extended m=7/8 metadata and result records only. "
             'No policy execution, demand-tape generation, paid request, or strategy/selection/parameter change occurred.', '']
    if result['status'] == 'timeout':
        lines += ['**Deferred: the finite 30-minute completion wait expired.** No complete-result claim is made.', '',
                  'Still missing or incomplete:'] + [f'- {name}' for name in result['pending']]
    else:
        lines += [f"**Status: {result['status']}; {result['check_count']} checks, {len(result['errors'])} failures.**", '',
                  f"Inspected {result['numeric_artifacts']} tuned/default numeric files, {result['numeric_scenario_rows']} numerical scenario rows "
                  f"({result['numeric_path_cost_values']:,} path costs), and {result['baek_scenario_rows']} Baek case records.", '',
                  'The audit independently reconstructs each full numeric test-request SHA256 from frozen code/theta, complete scenario dictionaries, '
                  'optimizer seed 1731 and prescribed **128 paths / 500 burn-in / 3000 scored periods / demand seed 18094001**. '
                  'It also checks selected/origin/baseline source hashes, refit theta, literal defaults, compiled-structure hashes, parameter declarations, '
                  'normalization metadata, caps, zero test nfev, scenario coverage and recorded transition counts.', '',
                  'Each Baek source is checked against its source seal, session hash and final code. All available per-case code hashes/settings and '
                  'aggregate rows are checked; the frozen prompt/helper hashes are compared with the manifest. Extended aggregates do not themselves '
                  'require a top-level policy hash: provenance is verified through every contained per-case hash and the separate source seal.', '',
                  f"Largest path-mean discrepancy: {result['max_mean_error']:.3g}; largest cost-versus-100×(waste+lost) discrepancy: "
                  f"{result['max_metric_cost_error']:.3g}. These consistency checks do not rank methods or interpret statistical significance.", '']
        if result['errors']:
            lines += ['Failed checks:'] + [f'- {name}' for name in result['errors']] + ['']
        if result['baek_missing']:
            lines += ['Deferred missing Baek cases:'] + [f'- {name}' for name in result['baek_missing']] + ['']
        if result['limitations']:
            lines += ['Additional provenance limits:'] + [f'- {name}' for name in result['limitations']] + ['']
        lines += ['Limits: this verifies agreement among local saved artifacts, not an independent replay or externally timestamped history. '
                  'Request fingerprints do not bind trusted evaluator/optimizer/compiler code or actual demand-tape bytes; no saved tape hash is '
                  'verified here. The retained implementation snapshots, manifest and execution amendment remain necessary. '
                  'This does not certify equal compute, spending, causal optimizer benefit, policy novelty or superiority.', '']
    lines += ['Evidence: [result.json](../output/overnight_search/20260917/extended/diagnostics/extended_result_audit/result.json), '
              'including hashes of every inspected evidence file; '
              '[implementation audit](overnight_implementation_audit.md).']
    Path('docs/overnight_extended_result_audit.md').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait-seconds', type=float, default=1800)
    args = parser.parse_args()
    deadline = time.monotonic() + max(0, min(args.wait_seconds, 1800))
    previous, last_log = None, 0.0
    while True:
        missing = pending()
        if not missing:
            break
        if missing != previous or time.monotonic() - last_log > 60:
            print(json.dumps(dict(status='waiting', remaining_files=len(missing), first_missing=missing[:5])), flush=True)
            previous, last_log = missing, time.monotonic()
        if time.monotonic() >= deadline:
            result = dict(audit_utc=datetime.now(timezone.utc).isoformat(), status='timeout', pending=missing)
            save(result)
            print(json.dumps(result), flush=True)
            return
        time.sleep(min(5, max(0, deadline - time.monotonic())))
    try:
        result = audit()
    except Exception as error:
        result = dict(audit_utc=datetime.now(timezone.utc).isoformat(), status='audit_error', error=repr(error))
        destination = RUN / 'diagnostics' / 'extended_result_audit'
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)
        raise
    save(result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('files_sha256', 'selected', 'numeric')}), flush=True)


if __name__ == '__main__':
    main()
