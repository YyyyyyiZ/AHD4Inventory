"""Execute a frozen policy in the existing OS sandbox and collect path costs."""
import ast
import base64
import io
import json
from pathlib import Path
import numpy as np

from .environment import PARAMS, summarize


def source_audit(code):
    tree = ast.parse(code)
    banned = {"os", "sys", "subprocess", "socket", "requests", "urllib", "pathlib",
              "inspect", "ctypes", "multiprocessing", "concurrent", "importlib"}
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [(node.module or "").split(".")[0]]
        if banned.intersection(names):
            raise ValueError("Final policy requests unavailable external/process access")
        if isinstance(node, ast.Name) and node.id in {"open", "__import__", "eval", "exec"}:
            raise ValueError("Final policy requests file access or dynamic code execution")


def score_code(sandbox, code, level, demand_sets, seed=732019, validate_only=False):
    source_audit(code)
    buf = io.BytesIO()
    np.savez_compressed(buf, **demand_sets)
    data = base64.b64encode(buf.getvalue()).decode()
    # Policy globals never contain the evaluation data. The final code is frozen
    # before this wrapper is assembled. Network and external files remain denied.
    wrapper = '''
import numpy as np, scipy, math, itertools, json, time, signal, random, base64, io
_params = PARAMS_LITERAL
np.random.seed(SEED_LITERAL)
random.seed(SEED_LITERAL)
def _alarm(signum, frame):
    raise TimeoutError('Initialization exceeded 600 seconds')
signal.signal(signal.SIGALRM, _alarm)
_ns = {'__name__':'frozen_policy', 'np':np, 'math':math, 'itertools':itertools, 'scipy':scipy}
_start = time.monotonic()
signal.setitimer(signal.ITIMER_REAL, 600)
exec(compile(CODE_LITERAL, 'frozen_policy.py', 'exec'), _ns)
_policy = _ns['design'](dict(_params)) if LEVEL_LITERAL == 'L2' else _ns['compute_order_amount']
signal.setitimer(signal.ITIMER_REAL, 0)
_setup = time.monotonic()-_start
if not callable(_policy):
    raise ValueError('Expected callable policy')
_sets = np.load(io.BytesIO(base64.b64decode(DATA_LITERAL)), allow_pickle=False)
_results = {}
_calls = 0
_start = time.monotonic()
for _name in _sets.files:
    _demands = _sets[_name]
    _parts = np.zeros((len(_demands), 5))
    for _i, _path in enumerate(_demands):
        np.random.seed(SEED_LITERAL + 10000 + _i)
        random.seed(SEED_LITERAL + 10000 + _i)
        _s = np.full(5, 5.0)
        for _t, _d in enumerate(_path):
            _q = _policy(tuple(np.rint(_s)))
            if isinstance(_q, (bool, np.bool_)) or not np.isscalar(_q):
                raise ValueError('Invalid non-scalar/bool order')
            _q = float(_q)
            if not np.isfinite(_q) or not 0 <= _q <= 10 or _q != round(_q):
                raise ValueError('Order is not an integer in [0,10]')
            _a, _b = _s[0], _s[1]
            _u = _d - _a - _b
            _c = np.array([9.025*_q, max(0.,_b-max(0.,_d-_a)),
                          2*max(0.,_u), 8*max(0.,_a-_d), 1000*max(0.,_u-10)])
            _parts[_i] += 0.95**_t * _c
            _s = np.array([max(_b-max(0.,_d-_a),-10), _s[2],_s[3],_s[4],_q])
            _calls += 1
    _results[_name] = {'path_costs':_parts.sum(axis=1).tolist(),
                      'component_means':_parts.mean(axis=0).tolist()}
print('PIC_RESULT_JSON='+json.dumps({'setup_seconds':_setup,
      'evaluation_seconds':time.monotonic()-_start, 'policy_calls':_calls,
      'random_seed':SEED_LITERAL, 'datasets':_results}, allow_nan=False))
'''
    for key, value in dict(PARAMS_LITERAL=repr(PARAMS), SEED_LITERAL=str(seed),
                           CODE_LITERAL=repr(code), LEVEL_LITERAL=repr(level),
                           DATA_LITERAL=repr(data)).items():
        wrapper = wrapper.replace(key, value)
    run = sandbox.run(wrapper, 900 if validate_only else 2400, max_output_bytes=262144)
    if run.returncode != 0 or run.timed_out:
        return dict(status="invalid" if not run.timed_out else "timeout", execution=run.to_dict())
    lines = [x for x in run.stdout.splitlines() if x.startswith("PIC_RESULT_JSON=")]
    if len(lines) != 1:
        return dict(status="invalid", error="No unique scoring result", execution=run.to_dict())
    result = json.loads(lines[0].split("=", 1)[1])
    for entry in result["datasets"].values():
        entry.update(summarize(entry["path_costs"]))
    result.update(status="valid", setup_over_target=result["setup_seconds"] > 30)
    return result


def synthetic_demands():
    return np.array([[0., 0., 0., 0., 0., 0., 0., 0.],
                     [10., 10., 10., 10., 10., 10., 10., 10.],
                     [5.2, 1.3, 9.9, 0.1, 6.7, 2.4, 8.9, 4.1],
                     [0., 10., 0., 10., 0., 10., 0., 10.]])
