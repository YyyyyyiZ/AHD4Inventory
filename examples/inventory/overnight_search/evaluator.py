"""Per-candidate killable sandbox with trusted simulator/optimizer preinstalled."""
import inspect
import json
from pathlib import Path
import sys
import time

from ..baek_comparison.sandbox import PythonSandbox
from ..correlated_benchmark import fast_policy

ROOT = Path(__file__).resolve().parent


class NumericalSandbox(PythonSandbox):
    def _profile(self, scratch):
        import numba, llvmlite
        text = super()._profile(scratch)
        for module in (numba, llvmlite):
            path = Path(module.__file__).resolve().parent
            text += '\n(allow file-read* (subpath '+json.dumps(str(path))+'))'
            for p in path.parent.glob(path.name+'*.dist-info'):
                text += '\n(allow file-read* (subpath '+json.dumps(str(p))+'))'
        return text


def prelude():
    raw = Path(fast_policy.__file__).read_text()
    # Keep the audited AST validator and constants; avoid its unrelated worker.
    raw = raw[:raw.index('\ndef _encode(')]
    # The OS sandbox isolates all external effects; the simulator gives copies
    # of state arrays, so local numerical working arrays are safe to mutate.
    raw = raw.replace('if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):',
                      'if False:')
    # The prompt permits math/numpy imports without restricting their scope.
    # Move only safe leading imports in AST; raw text/OPT_PARAM lines stay intact.
    parse_line = '    tree = ast.parse(code)\n'
    hash_field = '"code_sha256": hashlib.sha256(code.encode()).hexdigest()}'
    if raw.count(parse_line) != 1 or raw.count(hash_field) != 1:
        raise ValueError('Policy validator changed; review import normalization injection')
    raw = raw.replace(parse_line, '    tree, import_normalization = normalize_leading_policy_imports(ast.parse(code))\n')
    raw = raw.replace(hash_field, '"code_sha256": hashlib.sha256(code.encode()).hexdigest(), "import_normalization": import_normalization}')
    raw += '\n'+(ROOT/'normalization.py').read_text()
    raw += '\nARGUMENTS = ("age", "pipeline", "mu", "cv", "f", "L")\n'
    raw += (ROOT/'perishable.py').read_text().split('\nif __name__')[0].replace('from __future__ import annotations', '')
    raw += '\n'+(ROOT/'optimization.py').read_text()
    raw += '\n'+(ROOT/'numeric_job.py').read_text()
    return raw


def evaluate(job, timeout=240):
    sandbox = NumericalSandbox(sys.executable)
    code = prelude()+'\njob = '+repr(job)+'\nprint("JOB_RESULT="+json.dumps(run_numeric_job(job),allow_nan=False))\n'
    start = time.monotonic()
    result = sandbox.run(code, timeout_seconds=timeout, max_output_bytes=2_000_000)
    if result.returncode or result.timed_out:
        raise ValueError(('timeout' if result.timed_out else result.stderr)[-3500:])
    for line in reversed(result.stdout.splitlines()):
        if line.startswith('JOB_RESULT='):
            output = json.loads(line[len('JOB_RESULT='):])
            output['wall_seconds'] = time.monotonic()-start
            output['transitions'] = sum(x['nfev']+1 for x in output['results'].values())*job['paths']*(job['horizon']+job['burnin'])
            return output
    raise ValueError('Worker returned no record: '+result.stdout[-1000:])
