"""Read-only end-to-end sandbox audit of the integrated cache worker.

The selector is overridden only in an isolated scratch prelude; active source
and all real training/refit/validation/test seeds remain untouched.
"""
import ast
from dataclasses import asdict
import json
from pathlib import Path
import sys

from .evaluator import NumericalSandbox, prelude
from .perishable import scenarios


def main():
    root = Path('output/overnight_search/20260917')
    text = prelude()
    tree = ast.parse(text)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_numeric_job')
    assignments = [n for n in ast.walk(fn) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'cache_actions' for t in n.targets)]
    assert len(assignments) == 1
    assignments[0].value = ast.Constant(True)
    fn.name = 'run_cached_diagnostic'
    override = ast.unparse(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])))
    selected_scenarios = [s for s in scenarios()
                          if (s.m, s.cv, s.f) in ((3, 1.5, 0.0), (5, 2.0, 0.5))]
    requests = []
    for name in ('evolution_r2', 'evolution_r3'):
        selected = json.loads((root / 'selected' / (name + '.json')).read_text())['selected']
        requests.append(dict(method=name, op='fit', code=selected['code'],
                             scenarios=[asdict(s) for s in selected_scenarios],
                             paths=4, burnin=50, horizon=150, seed=98714011,
                             budget=17, optimizer_seed=98714012))
    checks = '''
records = []
for request in diagnostic_requests:
    original = run_numeric_job(request)
    cached = run_cached_diagnostic(request)
    assert original['action_cache']['enabled'] is False
    assert cached['action_cache']['enabled'] is True
    for field in ('parameters', 'structure_sha256', 'code_sha256', 'import_normalization'):
        assert original[field] == cached[field], field
    for name in original['results']:
        a, b = original['results'][name], cached['results'][name]
        for field in ('theta', 'cost', 'nfev', 'path_costs', 'metrics', 'cap'):
            assert a[field] == b[field], (name, field)
    records.append({'method': request['method'], 'scenarios': list(original['results']),
                    'fit_results_exact': True, 'metadata_exact': True,
                    'cached_stats': cached['action_cache']})
print('SANDBOX_PARITY=' + json.dumps(records, allow_nan=False))
'''
    sandbox = NumericalSandbox(sys.executable)
    result = sandbox.run(text + '\n' + override + '\ndiagnostic_requests=' + repr(requests)
                         + '\n' + checks, timeout_seconds=120, max_output_bytes=200_000)
    assert result.returncode == 0 and not result.timed_out, result.stderr
    record = next(line.split('=', 1)[1] for line in result.stdout.splitlines()
                  if line.startswith('SANDBOX_PARITY='))
    output = dict(seed=98714011, budget=17, optimizer_seed=98714012,
                  elapsed_seconds=result.elapsed_seconds, records=json.loads(record),
                  active_source_unchanged=True)
    destination = root / 'diagnostics' / 'memoization' / 'sandbox_parity.json'
    destination.write_text(json.dumps(output, indent=2))
    print(json.dumps(output), flush=True)


if __name__ == '__main__':
    main()
