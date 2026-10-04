"""Auditable Baek-style L2 sessions for the overnight perishable benchmark.

No model request runs on import. Uses an independent hard USD12 allocation,
durable reservations, and the established isolated full Python-tool protocol.
"""
from __future__ import annotations

import argparse
import ast
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import io
from pathlib import Path
import sys
import threading
import uuid

from examples.inventory.baek_comparison.harness import (
    BudgetExceeded, OpenRouterHarness, RunBudget, SessionConfig,
)
from examples.inventory.baek_comparison.sandbox import PythonSandbox


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUN = ROOT / "output/overnight_search/20260917/baek"
CREDENTIALS = Path.home() / ".config/ahd4inventory/openrouter_credentials.json"
LIMIT_USD = 12.0


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    tmp.replace(path)


def sha256(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class DurableBudget(RunBudget):
    """Thread-safe reservations durably written before a request may be sent.

    A process-wide file lock is held by generate(). A crashed request retains
    its bound unless its exact journal reservation has an authoritative cost.
    """
    def __init__(self, run_dir):
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / "budget.json"
        self._lock = threading.RLock()
        self._local = threading.local()
        if self.path.exists():
            self.ledger = json.loads(self.path.read_text())
            if self.ledger["limit_usd"] != LIMIT_USD:
                raise ValueError("The frozen USD12 allocation must not change")
        else:
            self.ledger = dict(limit_usd=LIMIT_USD, created_utc=utc_now(), requests={})
        super().__init__(LIMIT_USD)
        self._reconcile_recorded_responses()
        self._refresh()

    def _reconcile_recorded_responses(self):
        for log in self.run_dir.rglob("events.jsonl"):
            pending = None
            for line in log.read_text().splitlines():
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("event") == "request":
                    pending = event.get("budget_reservation_id")
                elif pending and event.get("event") in {"response", "request_rejected"}:
                    if event["event"] == "response":
                        cost = (event.get("response", {}).get("usage") or {}).get("cost")
                    else:
                        cost = 0.0 if event.get("known_pre_inference") else None
                    if isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(cost) and cost >= 0:
                        record = self.ledger["requests"].get(pending)
                        if record is None:
                            raise ValueError("Journal refers to a missing budget reservation")
                        record.update(state="known", actual_cost_usd=float(cost), reconciled_from=str(log))
                    pending = None

    def _refresh(self):
        records = self.ledger["requests"].values()
        self.spent_usd = sum(r.get("actual_cost_usd", 0.0) for r in records if r["state"] == "known")
        self.reserved_usd = sum(r["upper_usd"] for r in records if r["state"] != "known")
        self.ledger.update(known_cost_usd=self.spent_usd, held_upper_usd=self.reserved_usd,
                           committed_upper_usd=self.spent_usd + self.reserved_usd,
                           updated_utc=utc_now())
        atomic_json(self.path, self.ledger)

    def reserve(self, upper_cost):
        with self._lock:
            if not math.isfinite(upper_cost) or upper_cost < 0:
                raise ValueError("Invalid request upper bound")
            if self.spent_usd + self.reserved_usd + upper_cost > self.limit_usd + 1e-12:
                raise BudgetExceeded("Independent Baek allocation USD12 exhausted; no further request sent")
            if getattr(self._local, "reservation", None) is not None:
                raise RuntimeError("Previous request reservation was not settled")
            request_id = uuid.uuid4().hex
            self.ledger["requests"][request_id] = dict(state="pending", upper_usd=float(upper_cost),
                                                       reserved_utc=utc_now())
            self._local.reservation = request_id
            self._refresh()

    def current_reservation_id(self):
        return getattr(self._local, "reservation", None)

    def settle(self, upper_cost, actual_cost):
        with self._lock:
            request_id = self.current_reservation_id()
            if request_id is None:
                raise RuntimeError("No pending reservation in this request thread")
            row = self.ledger["requests"][request_id]
            if abs(row["upper_usd"] - upper_cost) > 1e-12:
                raise RuntimeError("Request reservation differs")
            if actual_cost is None:
                row.update(state="unknown_charge", settled_utc=utc_now())
            else:
                if not math.isfinite(actual_cost) or actual_cost < 0:
                    raise ValueError("Invalid actual request cost")
                row.update(state="known", actual_cost_usd=float(actual_cost), settled_utc=utc_now())
            self._local.reservation = None
            self._refresh()


class TrackedHarness(OpenRouterHarness):
    def _log(self, event, **fields):
        if event == "request":
            fields["budget_reservation_id"] = self.budget.current_reservation_id()
        return super()._log(event, **fields)


class PreludeSandbox(PythonSandbox):
    def __init__(self, *, prelude, python_executable, memory_limit_bytes=None):
        super().__init__(python_executable=python_executable)
        self.prelude = prelude
        self.memory_limit_bytes = memory_limit_bytes

    def _profile(self, scratch):
        import numba, llvmlite
        profile = super()._profile(scratch)
        for module in (numba, llvmlite):
            package = Path(module.__file__).resolve().parent
            profile += "\n(allow file-read* (subpath " + json.dumps(str(package)) + "))"
            for dist in package.parent.glob(package.name + "*.dist-info"):
                profile += "\n(allow file-read* (subpath " + json.dumps(str(dist)) + "))"
        return profile

    def run(self, code, timeout_seconds, max_output_bytes=65536):
        # Keep the helper source in its own compile unit so future imports in
        # submitted programs remain legal and tracebacks stay readable.
        combined = (f"exec(compile({self.prelude!r}, 'trusted_benchmark.py', 'exec'), globals())\n"
                    + f"exec(compile({code!r}, 'submitted_code.py', 'exec'), globals())\n")
        if self.memory_limit_bytes is not None:
            from .memory_guard import MemoryGuardMixin
            self.memory_poll_seconds = 0.1
            combined = ("import os,numba\nos.environ['NUMBA_BOUNDSCHECK']='1'\n"
                        "numba.config.BOUNDSCHECK=1\n" + combined)
            return MemoryGuardMixin.run(self, combined, timeout_seconds, max_output_bytes=max_output_bytes)
        return super().run(combined, timeout_seconds, max_output_bytes=max_output_bytes)


def build_prelude(*, train_seed=17091001, training_paths=8, burnin=200, horizon=512,
                  optimizer_budget=256):
    """Freeze exact model and common optimizer; exclude the evaluation grid."""
    directory = Path(__file__).resolve().parent
    tree = ast.parse((directory / "perishable.py").read_text())
    tree.body = [node for node in tree.body
                 if not (isinstance(node, ast.FunctionDef) and node.name in {"scenarios", "handcheck"})
                 and not (isinstance(node, ast.If) and "__name__" in ast.unparse(node.test))]
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in {"evaluate", "evaluate_python"}:
            node.args.defaults[-1] = ast.Constant(value=int(burnin))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "njit":
            for keyword in node.keywords:
                if keyword.arg == "cache":
                    keyword.value = ast.Constant(value=False)
    model_source = ast.unparse(ast.fix_missing_locations(tree))
    optimizer_source = (directory / "optimization.py").read_text().replace("budget=256", f"budget={int(optimizer_budget)}")
    wrappers = '''
def scenario_from_params(params):
    fields = {name: params[name] for name in Scenario.__dataclass_fields__ if name in params}
    fields.setdefault("name", "anonymous_instance")
    return Scenario(**fields)

def training_demands(params):
    return sample_demands(scenario_from_params(params), 8, 200+512, 17091001)

def simulate(policy, params, demands=None, *, npaths=8, burnin=200, horizon=512, seed=17091001):
    """Score arbitrary scalar policy(age,pipeline); return mean and path costs.

    Exact trusted transitions are used; attempts optional Numba acceleration,
    falling back to unrestricted Python callback evaluation if compilation fails.
    """
    s = scenario_from_params(params)
    if demands is None:
        demands = sample_demands(s, npaths, burnin+horizon, seed)
    backend = "python"
    try:
        compiled = policy if hasattr(policy, "py_func") else njit(policy)
        def adapter(age, pipeline, theta, mu, cv, f, L):
            return compiled(age, pipeline)
        fast = njit(adapter)
        costs, components = evaluate(s, demands, fast, np.empty(0), burnin)
        backend = "numba"
    except Exception:
        costs, components = evaluate_python(s, demands, policy, burnin)
    return {"mean_cost": float(costs.mean()), "path_costs": costs,
            "components": components, "backend": backend}
'''
    wrappers = (wrappers.replace("17091001", str(int(train_seed)))
                .replace("8, 200+512", f"{int(training_paths)}, {int(burnin)}+{int(horizon)}")
                .replace("npaths=8, burnin=200, horizon=512", f"npaths={int(training_paths)}, burnin={int(burnin)}, horizon={int(horizon)}"))
    source = model_source + "\n" + optimizer_source + "\n" + wrappers
    return source + "\nTRUSTED_BENCHMARK_SOURCE = " + repr(source) + "\n"


def make_prompt(*, shelf_lives=(3, 4, 5), train_seed=17091001, training_paths=8,
                burnin=200, horizon=512, optimizer_budget=256, memory_limit_bytes=None,
                initial_information=None):
    prompt = '''Design a reusable algorithm for the following CLASS of perishable inventory problems.
You receive the mathematical model and broad parameter ranges, not the target evaluation instance list.
Return Python source defining design(params), which returns a stationary order function policy(age,pipeline).
Choose any algorithmic representation or parameter count. Your task is to minimize expected long-run cost.

MODEL AND OBSERVATIONS
One product has integer inventory. At a decision epoch, age is a length-m int64 array ordered by
remaining shelf life 1,2,...,m, and already includes today's receipts. pipeline is length L-1:
pipeline[k-1] is old quantity arriving k periods from now. Decide a nonnegative order q;
it arrives L periods later, with m usable periods of fresh shelf life. There are no clocks,
future-demand observations, episode indexes, or persistent policy memory. Use only current state and fixed params.
The simulator projects every method's action identically: first max(0, q), then clip to
max(0, cap - sum(age) - sum(pipeline)), then round with numpy.rint (half to even).
Thus cap constrains current inventory POSITION, not just the amount ordered or the on-hand stock.

After ordering, two independent demands are realized. Serve the FIFO group first using oldest stock first;
then serve the LIFO group using freshest stock first. Unmet demand is lost. Any remaining stock with one
usable period expires. The surviving stock ages one period; the next period's due orders then arrive fresh.
The per-period cost is w*(expired units) + p*(lost units) + h*(surviving units). No purchasing or fixed order costs.

DEMAND LAW (exact known distribution, not just moment information)
Total demand mean is mean, its standard deviation is cv*mean; cv is the ordinary coefficient of variation.
FIFO and LIFO demands are INDEPENDENT nonnegative-integer two-moment Adan--van Eenige--Resing distributions.
FIFO mean = f*mean, variance = f*(cv*mean)^2. LIFO mean = (1-f)*mean, variance = (1-f)*(cv*mean)^2.
These are not binomial shares of one sampled total demand and need not be a single negative-binomial law.
The preloaded _aer_components and aer_pmf implement the exact distribution; sample_demands samples it.
Across periods all demands are independent. No law needs to be estimated.
cap is the smallest integer q whose cumulative probability under the sum of (m+L) iid TOTAL demands
is at least p/(p+w), computed by the supplied inventory_cap. It is not a high-percentile safety limit.

PARAMETERS
The problem class has shelf life m in {3,4,5}, lead time L=2, mean=4,
ordinary demand CV cv in {1.5,2}, FIFO fraction f in {0,0.5}, h=0, p=100, w=100,
with demand_mode='paper_cv', cap_mode='paper'. These family specifications are common to all approaches.
It may also contain name, actual_cv, and inventory_cap for reporting; ignore additional reporting keys.
This is an explicitly specified extension of the Baek L2 design protocol to perishable inventory.

COMMON TRUSTED COMPUTATION PROVIDED TO EVERY TOOL CALL AND FINAL DESIGN
The following helpers are already loaded, with no access to any validation/test demands:
  Scenario(name,m,L,cv,f,mean=4,h=0,p=100,w=100,demand_mode='paper_cv',cap_mode='paper')
  scenario_from_params(params) -> Scenario
  _aer_components(mean,sd) -> (mixture weight, SciPy discrete distribution) pairs
  aer_pmf(mean,sd) -> NumPy probability mass array, tail below 1e-13 numerically removed
  inventory_cap(scenario) -> int; sample_demands(scenario,npaths,periods,seed) -> [npaths,periods,2] integer array
  evaluate_python(scenario,demands,policy,burnin=200) -> (per_path_cost_per_period,per_path_[waste,lost,order])
  training_demands(params) -> common training sample, 8 paths of 200+512 periods, seed=17091001
  simulate(policy,params,demands=None,npaths=8,burnin=200,horizon=512,seed=17091001)
      -> dict(mean_cost,path_costs,components,backend); arbitrary policy(age,pipeline) accepted.
  evaluate(scenario,demands,numba_policy,theta,burnin=200) -> same arrays as evaluate_python.
      For this fast parameterized helper only: numba_policy(age,pipeline,theta,mu,cv,f,L) returns scalar q.
  optimize(objective,bounds,initial,budget=256,seed=1) -> dict(theta,cost,nfev,seconds).
      This is the same 256-evaluation, 16-population differential-evolution helper available to the competing workflow.
You may use or replace these helpers; they do not constrain your final algorithm. numpy as np, scipy, numba.njit,
and Python standard libraries are available. TRUSTED_BENCHMARK_SOURCE contains full helper source for inspection.
Numba acceleration and shared simulator/optimizer access are explicit favorable adaptations to the original protocol.
Simulation begins empty with ordinary demand during an unscored burn-in. Default training uses 200 burn-in +512
scored periods on 8 paths; independent evaluation uses longer trajectories. You may generate your own samples.
No zero-demand stocking periods and no terminal salvage value are used.

COMPUTATION BUDGET
You have 3,600 seconds cumulative run_python execution across at most 50 calls, shared across all development
and experiments in this session. Each call is a fresh process: re-define your own variables/functions each time;
the trusted helpers are reloaded automatically. Test and revise any approach within this budget.
Final design(params) may do instance-specific computation, including simulation and optimization. Aim to finish
within 30 seconds per instance; a 600-second hang guard is used and actual setup time is recorded.
The returned policy(age,pipeline) must be lightweight, deterministic, and stationary. It must not invoke an LLM,
read files, use networking, or access future demand. Helper functions, arbitrary fixed tables, NumPy, SciPy and
Numba are allowed; there is no numerical-parameter-count limit. Final helpers provided above remain available.
Return your final complete source in one Python code block, defining design(params). No prose after the code.
'''
    lives = ",".join(str(int(x)) for x in shelf_lives)
    prompt = (prompt.replace("m in {3,4,5}", "m in {" + lives + "}")
              .replace("17091001", str(int(train_seed)))
              .replace("burnin=200", f"burnin={int(burnin)}")
              .replace("npaths=8", f"npaths={int(training_paths)}")
              .replace("horizon=512", f"horizon={int(horizon)}")
              .replace("8 paths of 200+512 periods", f"{int(training_paths)} paths of {int(burnin)}+{int(horizon)} periods")
              .replace("budget=256", f"budget={int(optimizer_budget)}")
              .replace("256-evaluation", f"{int(optimizer_budget)}-evaluation")
              .replace("200 burn-in +512\nscored periods on 8 paths", f"{int(burnin)} burn-in +{int(horizon)}\nscored periods on {int(training_paths)} paths"))
    if memory_limit_bytes is not None:
        prompt += (f"\nMACHINE RESOURCE CONSTRAINT: every numerical worker, for all compared methods, has a "
                   f"{int(memory_limit_bytes)}-byte (1 GiB) resident-memory limit on the shared 8 GiB machine. "
                   "A resident-memory watchdog terminates a worker that exceeds this limit; memory failures are reported explicitly.\n")
    if initial_information is not None:
        prompt += ("\nCOMMON INITIAL INFORMATION\n"
                   "The identical initial policy and training diagnostics below are supplied to every comparison arm. "
                   "This is an explicit common-seed extension of the Baek-style tool-enabled L2 protocol. "
                   "There is no restriction on retaining, changing, or replacing this initial policy. "
                   "All numbers below come only from the common training sample.\n"
                   + initial_information + "\n")
    return prompt


def score_code(code, params, demands, *, burnin, run_dir=DEFAULT_RUN, timeout=1200):
    """Isolated score for arbitrary Baek design source on caller's exact tapes.

    Policy setup has a 600-second guard. This function never reads credentials
    or calls a model; final costs are returned to the caller, never generation.
    """
    import numpy as np
    source = (Path(run_dir) / "trusted_prelude.py").read_text()
    manifest = json.loads((Path(run_dir) / "manifest.json").read_text())
    memory_limit = manifest["identity"].get("memory_limit_bytes")
    buffer = io.BytesIO()
    np.savez_compressed(buffer, demands=np.asarray(demands, dtype=np.int64))
    packed = base64.b64encode(buffer.getvalue()).decode()
    worker = f'''
import base64, io, json, signal, time, types, sys, os, numba
# Evaluation-only amendment: runtime config overrides even a returned
# decorator's boundscheck=False, preventing silent out-of-bounds reads.
os.environ['NUMBA_BOUNDSCHECK'] = '1'
numba.config.BOUNDSCHECK = 1
_policy_module = types.ModuleType('frozen_baek_policy')
_policy_module.__dict__.update(globals())
_policy_module.__dict__['__name__'] = 'frozen_baek_policy'
_artifact_file = os.path.join(os.getcwd(), 'frozen_baek_policy.py')
with open(_artifact_file, 'w') as _artifact_handle:
    _artifact_handle.write({code!r})
_policy_module.__dict__['__file__'] = _artifact_file
sys.modules['frozen_baek_policy'] = _policy_module
params = {params!r}
_t0 = time.monotonic()
signal.alarm(600)
exec(compile({code!r}, _artifact_file, 'exec'), _policy_module.__dict__)
_policy = _policy_module.design(params)
if not callable(_policy):
    raise TypeError('design(params) must return a callable')
_setup_seconds = time.monotonic()-_t0
signal.alarm(0)
_s = scenario_from_params(params)
_cap = inventory_cap(_s)
_probe_rng = np.random.default_rng(918361)
_probe_states = []
for _i in range(24):
    _units = 0 if _i == 0 else int(_probe_rng.integers(0, _cap+1))
    _n = _s.m + max(0, _s.L-1)
    _counts = _probe_rng.multinomial(_units, np.ones(_n)/_n).astype(np.int64)
    _probe_states.append((_counts[:_s.m], _counts[_s.m:]))
def _probe_action(_state):
    _age, _pipeline = _state
    _raw = float(_policy(_age.copy(), _pipeline.copy()))
    if not np.isfinite(_raw):
        raise ValueError('Nonfinite action in synthetic stationary-policy probe')
    return int(np.rint(min(max(0., _raw), max(0, _cap-_age.sum()-_pipeline.sum()))))
_probe_first = [_probe_action(_state) for _state in _probe_states]
_probe_again = [_probe_action(_state) for _state in reversed(_probe_states)][::-1]
if _probe_first != _probe_again:
    raise ValueError('Effective action changes for the same state across probe order')
_demands = np.load(io.BytesIO(base64.b64decode({packed!r})), allow_pickle=False)['demands']
_t1 = time.monotonic()
_answer = simulate(_policy, params, _demands, burnin={int(burnin)})
_answer['path_costs'] = _answer['path_costs'].tolist()
_answer['components'] = _answer['components'].tolist()
_answer['setup_seconds'] = _setup_seconds
_answer['score_seconds'] = time.monotonic()-_t1
_answer['numba_boundscheck_enforced'] = True
_answer['synthetic_probe_actions'] = _probe_first
_answer['stationary_probe_passed'] = True
print('BAEK_SCORE='+json.dumps(_answer,allow_nan=False))
'''
    sandbox = PreludeSandbox(prelude=source, python_executable=sys.executable,
                             memory_limit_bytes=memory_limit)
    result = sandbox.run(worker, timeout_seconds=timeout, max_output_bytes=8_000_000)
    if result.returncode or result.timed_out:
        raise RuntimeError("Baek scoring failed: " + (result.stderr[-4000:] if result.stderr else str(result.to_dict())))
    lines = [line[len("BAEK_SCORE="):] for line in result.stdout.splitlines() if line.startswith("BAEK_SCORE=")]
    if len(lines) != 1:
        raise RuntimeError("Missing or ambiguous Baek score marker")
    answer = json.loads(lines[0])
    answer["sandbox_elapsed_seconds"] = result.elapsed_seconds
    answer["memory_limit_bytes"] = memory_limit
    answer["observed_peak_rss_bytes"] = getattr(result, "observed_peak_rss_bytes", None)
    return answer


def prepare(run_dir, *, prompt, prelude, memory_limit_bytes=None, common_initial_information_sha256=None):
    run_dir = Path(run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    identity = dict(protocol="Baek-L2-perishable-known-generator-tools-v1", model="openai/gpt-5.6-sol",
                    reasoning_effort="high", sessions=3, python_budget_seconds_per_session=3600,
                    max_tool_calls_per_session=50, hard_global_allocation_usd=LIMIT_USD,
                    setup_target_seconds=30, setup_guard_seconds=600,
                    prompt_sha256=sha256(prompt), trusted_prelude_sha256=sha256(prelude),
                    independent_draw_selection="All submitted valid draws; no score-based replacement",
                    adaptation="Perishable inventory; supplied trusted simulator and shared optimizer helpers; deterministic order rules")
    if memory_limit_bytes is not None:
        identity["memory_limit_bytes"] = int(memory_limit_bytes)
        identity["memory_guard"] = "0.1-second parent RSS watchdog, whole-worker-group termination"
    if common_initial_information_sha256 is not None:
        identity["protocol"] = "Baek-style-L2-perishable-common-seed-tools-v2"
        identity["common_initial_information_sha256"] = common_initial_information_sha256
        identity["adaptation"] += "; common initial policy and training diagnostics given identically to all arms"
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        saved = json.loads(manifest_path.read_text())
        if saved["identity"] != identity:
            raise ValueError("Frozen Baek prompt/helper/protocol differs; use a new run")
    else:
        atomic_json(manifest_path, dict(identity=identity, created_utc=utc_now(), python=sys.version))
    for name, source in (("prompt.txt", prompt), ("trusted_prelude.py", prelude)):
        target = run_dir / name
        if target.exists() and target.read_text() != source:
            raise ValueError("Frozen source differs: " + name)
        if not target.exists():
            target.write_text(source)
    return identity


def resolve_budget_directory(run_dir, budget_dir=None):
    """Honor the immutable saved allocation before any credential read or POST."""
    root = Path(run_dir).resolve()
    allocation = root / "budget_allocation.json"
    if allocation.exists():
        saved = json.loads(allocation.read_text())
        if saved.get("global_shared_limit_usd") != LIMIT_USD:
            raise ValueError("Saved shared allocation differs from the hard USD12 limit")
        recorded_root = Path(saved["global_budget_directory"]).resolve()
        if budget_dir is not None and Path(budget_dir).resolve() != recorded_root:
            raise ValueError("Explicit budget directory conflicts with the immutable saved shared allocation")
        budget_root = recorded_root
    else:
        # The prospective phase2 location must never create its own USD12 pool,
        # including if its allocation metadata was accidentally removed.
        inherited = DEFAULT_RUN.resolve() if root == (DEFAULT_RUN / "extended").resolve() else root
        budget_root = Path(budget_dir).resolve() if budget_dir is not None else inherited
        if root == (DEFAULT_RUN / "extended").resolve() and budget_root != DEFAULT_RUN.resolve():
            raise ValueError("The extended experiment must share the original Baek USD12 ledger")
    if root == (DEFAULT_RUN / "extended").resolve() and budget_root != DEFAULT_RUN.resolve():
        raise ValueError("The extended experiment must share the original Baek USD12 ledger")
    if not root.is_relative_to(budget_root):
        raise ValueError("Shared run must lie under its budget directory for journal reconciliation")
    return budget_root


def generate(run_dir=DEFAULT_RUN, *, workers=3, only=None, budget_dir=None):
    root = Path(run_dir).resolve()
    budget_root = resolve_budget_directory(root, budget_dir)
    manifest = json.loads((root / "manifest.json").read_text())["identity"]
    prompt = (root / "prompt.txt").read_text()
    prelude = (root / "trusted_prelude.py").read_text()
    if sha256(prompt) != manifest["prompt_sha256"] or sha256(prelude) != manifest["trusted_prelude_sha256"]:
        raise ValueError("Frozen prompt/helper source was modified")
    lock = (budget_root / ".runner.lock").open("a+")
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise RuntimeError("A Baek generator is already running") from None
    try:
        budget = DurableBudget(budget_root)
        if not (root / "budget_allocation.json").exists():
            atomic_json(root / "budget_allocation.json", dict(global_budget_directory=str(budget_root),
                                                              global_shared_limit_usd=LIMIT_USD,
                                                              new_additional_allocation_usd=0.0))
        key = json.loads(CREDENTIALS.read_text())["api_key"]
        sandbox = PreludeSandbox(prelude=prelude, python_executable=sys.executable,
                                 memory_limit_bytes=manifest.get("memory_limit_bytes"))
        sandbox.probe()
        sessions = [f"l2_r{x}" for x in range(1, 4) if only is None or f"l2_r{x}" == only]
        if not sessions:
            raise ValueError("Unknown session")
        todo = []
        for session in sessions:
            folder = root / "sessions" / session
            folder.mkdir(parents=True, exist_ok=True)
            if (folder / "result.json").exists():
                continue
            if (folder / "events.jsonl").exists():
                raise RuntimeError("Unfinished session already has a request journal; no automatic re-POST")
            todo.append(session)

        def run_one(session):
            folder = root / "sessions" / session
            print(json.dumps(dict(event="starting", session=session)), flush=True)
            harness = TrackedHarness(api_key=key, sandbox=sandbox, budget=budget,
                                     log_path=folder / "events.jsonl", config=SessionConfig(level="L2"))
            result = harness.run(prompt)
            record = dict(session=session, **asdict(result), finished_utc=utc_now())
            if result.final_code:
                (folder / "policy.py").write_text(result.final_code)
                record["code_sha256"] = sha256(result.final_code)
            atomic_json(folder / "result.json", record)
            print(json.dumps({k: record.get(k) for k in ("session", "status", "cost_usd", "tool_calls", "python_seconds")}), flush=True)
            return record

        results = []
        with ThreadPoolExecutor(max_workers=max(1, min(workers, 3))) as pool:
            futures = {pool.submit(run_one, s): s for s in todo}
            for future in as_completed(futures):
                results.append(future.result())
        return results
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


def status(run_dir=DEFAULT_RUN, *, budget_dir=None):
    root = Path(run_dir)
    rows = []
    for folder in sorted((root / "sessions").glob("*")):
        result = folder / "result.json"
        if result.exists():
            record = json.loads(result.read_text())
            rows.append({k: record.get(k) for k in ("session", "status", "cost_usd", "tool_calls", "python_seconds")})
        else:
            journal = folder / "events.jsonl"
            events = []
            if journal.exists():
                for line in journal.read_text().splitlines():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            rows.append(dict(session=folder.name, status="running_or_interrupted", events=len(events),
                             last_event=events[-1].get("event") if events else None))
    if budget_dir is None and (root / "budget_allocation.json").exists():
        budget_dir = json.loads((root / "budget_allocation.json").read_text())["global_budget_directory"]
    budget_root = Path(budget_dir) if budget_dir is not None else root
    ledger = json.loads((budget_root / "budget.json").read_text()) if (budget_root / "budget.json").exists() else {}
    return dict(sessions=rows, budget={k: ledger.get(k) for k in ("limit_usd", "known_cost_usd", "held_upper_usd", "committed_upper_usd")})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate", "status"])
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--only")
    parser.add_argument("--budget-dir", type=Path)
    args = parser.parse_args()
    if args.command == "generate":
        generate(args.run_dir, workers=args.workers, only=args.only, budget_dir=args.budget_dir)
    print(json.dumps(status(args.run_dir, budget_dir=args.budget_dir), indent=2))
