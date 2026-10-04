"""Isolated adapter retaining the repository's EOH -> m2 -> SciPy search chain.

Old source files are loaded under a private package and never edited. The
adapter replaces transport, numerical evaluation and prompts, while retaining
the generation loop, single-best-parent m2 selection, greedy survival and
L-BFGS-B parameter optimization. Saved candidates can be replayed on resume.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
import gzip
import fcntl
from functools import wraps
import hashlib
import importlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import time

import numpy as np

from .data import _arrays_hash
from .fast_policy import prepare_policy
from .problem import TrainingProblem
from .prompts import M2_TEMPLATE, TrainingAnalyzer


_FRAMEWORK = "_correlated_eoh_framework"


def _framework_modules():
    source = Path(__file__).resolve().parents[3]/'eoh/src/eoh'
    if _FRAMEWORK not in sys.modules:
        spec = importlib.util.spec_from_file_location(_FRAMEWORK, source/'__init__.py',
                                                       submodule_search_locations=[str(source)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[_FRAMEWORK] = module
        spec.loader.exec_module(module)
    names = {'eoh': 'methods.eoh.eoh', 'interface': 'methods.eoh.eoh_interface_EC',
             'evolution': 'methods.eoh.eoh_evolution', 'selection': 'methods.selection.best_deterministic',
             'management': 'methods.management.pop_greedy', 'paras': 'utils.getParas',
             'analyzer': 'problems.optimization.inventory.analyze'}
    return {key: importlib.import_module(_FRAMEWORK+'.'+value) for key, value in names.items()}


def _clean(value):
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items() if k not in {'test_obj', 'test_objective'}}
    if isinstance(value, (list, tuple)):
        return [_clean(x) for x in value]
    if isinstance(value, np.ndarray):
        return _clean(value.tolist())
    if isinstance(value, np.generic):
        return _clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp')
    text = json.dumps(_clean(value), ensure_ascii=False, allow_nan=False, indent=2)
    if path.suffix == '.gz':
        with gzip.open(temporary, 'wt', encoding='utf-8') as f:
            f.write(text)
    else:
        temporary.write_text(text)
    temporary.replace(path)


def _read(path):
    if Path(path).suffix == '.gz':
        with gzip.open(path, 'rt') as f:
            return json.load(f)
    return json.loads(Path(path).read_text())


def _restore_internal(individual):
    answer = dict(individual)
    answer['test_objective'] = float('nan')
    return answer


def _parse_response(response, max_opt_params):
    explanation = re.search(r'\{\{(.*?)\}\}', response, re.S)
    fences = re.findall(r'```(?:python)?\s*\n(.*?)```', response, re.S)
    if fences:
        code = fences[0].strip()
    else:
        text = response[:explanation.start()] if explanation else response
        start = re.search(r'^(?:import |from |def )', text, re.M)
        if not start:
            raise ValueError("No policy source found")
        code = text[start.start():].strip()
    prepared = prepare_policy(code, max_opt_params)
    return code+'\n', explanation.group(1).strip() if explanation else '', prepared['opt_params']


def _seed_code(problem):
    mean = float(problem.train_tapes['demands'][:, :problem.burnin+problem.horizon].mean())
    target = mean*(problem.scenario.mean_lead_time+1)
    upper = max(target*4, 1.)
    return (
        'def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):\n'
        f"    target = {target!r}  # OPT_PARAM: {{'initial': {target!r}, 'min': 0.0, 'max': {upper!r}, 'type': 'float'}}\n"
        '    order_amount = max(0.0, target - on_hand_inventory - sum(pipeline_orders))\n'
        '    return order_amount\n')


class _GatewayState:
    def __init__(self, client, output, max_opt_params, base_metadata):
        self.client, self.output = client, output
        self.max_opt_params, self.base_metadata = max_opt_params, base_metadata
        self.context, self.usage, self.calls = {}, [], 0
        self.fatal = None

    def start(self, context):
        self.context, self.usage, self.calls = dict(context), [], 0

    def _recover_client_response(self, metadata):
        """Replay only an already-accounted, exact-context provider response."""
        root = getattr(self.client, 'run_dir', None)
        if root is None:
            return None
        root = Path(root)
        ledger_path = root/'api_budget.json'
        ledger = _read(ledger_path) if ledger_path.exists() else {}
        matches = []
        for path in sorted((root/'api_requests').glob('*/request.json')):
            if _read(path).get('metadata') == metadata:
                matches.append(path)
        if len(matches) > 1:
            raise RuntimeError('Multiple provider requests match one candidate attempt; reconcile before resume')
        if not matches:
            return None
        request = matches[0]
        request_id = request.parent.name
        accounting = ledger.get('requests', {}).get(request_id, {})
        response_path = request.parent/'response.json'
        if (not response_path.exists() or accounting.get('state') not in {'complete', 'missing_cost'}
                or accounting.get('reservation_exceeded')):
            raise RuntimeError('Matching provider request is not safely replayable; no re-POST permitted')
        response = _read(response_path)
        expected_model = getattr(self.client, 'model', None)
        if expected_model is not None and response.get('model') != expected_model:
            raise RuntimeError('Saved provider response model differs from the requested model; no replay or re-POST permitted')
        choices = response.get('choices') or []
        content = choices[0].get('message', {}).get('content') if choices else None
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError('Saved provider response has no usable content; no automatic re-POST')
        usage = {**(response.get('usage') or {}), 'request_id': request_id, 'model': response.get('model'),
                 'provider': response.get('provider'), 'finish_reason': choices[0].get('finish_reason')}
        return content, usage

    def get_response(self, prompt):
        if self.fatal is not None:
            raise self.fatal
        if self.calls >= 2:
            raise ValueError("At most two model requests are permitted per candidate")
        self.calls += 1
        metadata = {**self.base_metadata, **self.context, 'candidate_attempt': self.calls,
                    'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
        record_key = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
        response_path = self.output/'model_responses'/f'{record_key}.json'
        if response_path.exists():
            saved = _read(response_path)
            if saved.get('metadata') != metadata:
                raise ValueError('Saved model-response identity mismatch')
            if saved.get('state') == 'complete':
                self.usage.append(saved['usage'])
                return saved['content']
        else:
            saved = None
        started = time.monotonic()
        try:
            recovered = self._recover_client_response(metadata)
            if recovered is not None:
                content, usage = recovered
            else:
                if saved is not None:
                    raise RuntimeError('Candidate request was interrupted; no recorded response and no automatic re-POST')
                _atomic(response_path, {'state': 'pending', 'metadata': metadata})
                content, usage = self.client.chat([{'role': 'user', 'content': prompt}], max_tokens=4096,
                                                  temperature=.7, metadata=metadata)
            # Persist response before parsing, evaluation or optimization can fail.
            _atomic(response_path, {'state': 'complete', 'metadata': metadata, 'content': content, 'usage': usage})
        except Exception as exc:
            self.fatal = exc
            _atomic(self.output/'blocked_transport.json', {'status': 'blocked', 'metadata': metadata,
                                                          'error_type': type(exc).__name__, 'error': str(exc),
                                                          'instruction': 'No automatic retry or re-POST. Review request accounting before resume.'})
            raise
        self.usage.append(dict(usage))
        with (self.output/'model_usage.jsonl').open('a') as f:
            f.write(json.dumps(_clean({**metadata, 'usage': usage, 'elapsed_seconds': time.monotonic()-started}),
                               allow_nan=False)+'\n')
        return content


def _exclusive_chain(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        output = Path(kwargs['output_dir']).resolve()
        output.mkdir(parents=True, exist_ok=True)
        with (output/'.chain.lock').open('a+') as handle:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('Another process is already running this evolution chain') from None
            try:
                return function(*args, **kwargs)
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return wrapped


@_exclusive_chain
def run_evolution(*, scenario, train_tapes, output_dir, client, population_size=10, generations=10,
                  optimizer_maxiter=15, max_opt_params=4, burnin=500, horizon=200, repeat=1,
                  resume=True, model_name='deepseek/deepseek-chat-v3-0324', evaluation_timeout=180.):
    """Run one scenario/repeat using training tapes only; no test paths accepted."""
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name in ('pops', 'pops_best', 'prompt_for_code', 'candidates'):
        (output/name).mkdir(exist_ok=True)
    if (output/'blocked_transport.json').exists():
        raise RuntimeError("This chain has an unresolved transport/accounting stop; no automatic resume")
    framework = _framework_modules()
    fingerprint_files = [framework[name].__file__ for name in ('eoh', 'interface', 'evolution', 'selection', 'management')]
    optimizer_path = Path(framework['eoh'].__file__).with_name('external_scipy.py')
    fingerprint_files.append(str(optimizer_path))
    identity = dict(scenario=scenario.to_dict(), training_arrays_sha256=_arrays_hash(train_tapes),
                    population_size=int(population_size), generations=int(generations),
                    optimizer='SciPy L-BFGS-B', optimizer_maxiter=int(optimizer_maxiter), optimizer_eps=.1,
                    max_opt_params=int(max_opt_params), burnin=int(burnin), horizon=int(horizon), repeat=int(repeat),
                    model=model_name, operator='m2', actual_parent_count=1, inner_workers=1,
                    feedback='compact training summaries; all cost feedback excludes burn-in',
                    compact_optimizer_feedback=True, final_code_feedback='full matrices re-evaluated after optimization',
                    test_access=False, max_model_requests_per_candidate=2,
                    adaptation_files={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                      for name in ('evolution.py', 'problem.py', 'prompts.py', 'fast_policy.py',
                                                   'data.py', 'environment.py')},
                    framework_files={p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in fingerprint_files})
    identity = _clean(identity)
    identity_path = output/'search_definition.json'
    if identity_path.exists():
        if not resume or _read(identity_path) != identity:
            raise ValueError("Existing search definition differs or resume is disabled")
    else:
        _atomic(identity_path, identity)
    state = _GatewayState(client, output, max_opt_params,
                          {'scenario_id': scenario.scenario_id, 'repeat': int(repeat), 'chain_dir': str(output)})
    problem = TrainingProblem(scenario, train_tapes, output_dir=output, burnin=burnin, horizon=horizon,
                              evaluation_timeout=evaluation_timeout, max_opt_params=max_opt_params)
    core_eoh, core_interface, core_evolution = framework['eoh'].EOH, framework['interface'].InterfaceEC, framework['evolution'].Evolution

    class Gateway:
        def __init__(self, *_args, **_kwargs):
            pass
        def get_response(self, prompt):
            return state.get_response(prompt)

    class AdaptedEvolution(core_evolution):
        def init_base_prompt(self):
            super().init_base_prompt()
            self.prompt_m2 = M2_TEMPLATE

        def _get_alg(self, prompt):
            error = None
            while state.calls < 2:
                response = self.interface_llm.get_response(prompt)
                try:
                    code, explanation, params = _parse_response(response, max_opt_params)
                    return [code, explanation, params, None]
                except (SyntaxError, ValueError, TypeError, KeyError) as exc:
                    error = exc
            raise ValueError('Invalid candidate after permitted requests: '+str(error))

    class AdaptedInterface(core_interface):
        def _refresh_feedback(self, individual):
            if not individual.get('code') or individual.get('objective') is None:
                return individual
            fitness = problem.evaluate(individual['code'])
            individual.update(objective=float(np.round(fitness['avg'], 5)), test_objective=float('nan'),
                              lower=float(np.round(fitness['lower'], 5)), upper=float(np.round(fitness['upper'], 5)),
                              trajectory=fitness['trajectory'], order_matrix=fitness['order_matrix'],
                              cost_matrix=fitness['cost_matrix'])
            return individual

        def optimize_individual(self, individual):
            source_hash = hashlib.sha256(individual['code'].encode()).hexdigest()
            path = output/'seed_optimization'/f'{source_hash}.json.gz'
            if path.exists():
                saved = _read(path)
                if saved.get('input_code_sha256') != source_hash:
                    raise ValueError('Seed optimization identity mismatch')
                return _restore_internal(saved['individual'])
            with problem.optimizer_feedback():
                optimized = super().optimize_individual(individual)
            answer = self._refresh_feedback(optimized)
            _atomic(path, {'input_code_sha256': source_hash, 'individual': answer})
            return answer

        def get_algorithm(self, pop, operator, n_pop=1):
            self._slot = 0
            answer = super().get_algorithm(pop, operator, n_pop)
            if state.fatal is not None:
                raise state.fatal
            return answer

        def get_offspring(self, pop, operator, n_pop):
            slot = self._slot
            self._slot += 1
            parents = self.select.parent_selection(pop, 1)
            parent_hash = hashlib.sha256(parents[0]['code'].encode()).hexdigest()
            context = {'generation': int(n_pop)+1, 'operator': operator, 'candidate_index': slot,
                       'parent_code_sha256': parent_hash}
            path = output/'candidates'/f'g{n_pop+1:03d}_{operator}_{slot:03d}.json.gz'
            if path.exists():
                record = _read(path)
                if record['context'] != context:
                    state.fatal = ValueError('Saved candidate parent/slot differs; refusing replay')
                    raise state.fatal
                code = record['offspring'].get('code')
                if record.get('code_sha256') != (hashlib.sha256(code.encode()).hexdigest() if code else None):
                    state.fatal = ValueError('Saved candidate code hash mismatch')
                    raise state.fatal
                return parents, _restore_internal(record['offspring'])
            state.start(context)
            problem.context = context
            before = problem.evaluations
            with problem.optimizer_feedback():
                result = super().get_offspring(pop, operator, n_pop)
            if state.fatal is not None:
                raise state.fatal
            result = (result[0], self._refresh_feedback(result[1]))
            _atomic(path, {'context': context, 'offspring': result[1], 'usage': state.usage,
                           'code_sha256': (hashlib.sha256(result[1]['code'].encode()).hexdigest()
                                           if result[1].get('code') else None),
                           'model_requests': state.calls, 'training_evaluations': problem.evaluations-before,
                           'optimizer': {'name': 'L-BFGS-B', 'maxiter': optimizer_maxiter, 'eps': .1,
                                         'only_training_objective': True}})
            return result

    class AdaptedEOH(core_eoh):
        @staticmethod
        def _json_ready_individual(indiv):
            # Preserve the concise algorithm explanation, unlike the legacy writer.
            if indiv is None:
                return None
            return _clean({k: v for k, v in indiv.items()
                           if k not in {'trajectory', 'cost_matrix', 'order_matrix'}})

        def save_results(self, population, pop_idx, mode='train'):
            if mode != 'train':
                return
            super().save_results(population, pop_idx, mode)
            checkpoint = {'generation': pop_idx, 'population': population,
                          'best_code_sha256': hashlib.sha256(population[0]['code'].encode()).hexdigest(),
                          'best_train_cost': population[0]['objective'], 'test_evaluated': False}
            _atomic(output/'checkpoints'/f'g{pop_idx:03d}.json.gz', checkpoint)
            _atomic(output/'progress.json', {k: v for k, v in checkpoint.items() if k != 'population'})

    paras = framework['paras'].Paras()
    paras.set_paras(method='eoh', problem='inventory', dist=scenario.scenario_id,
                    n_train=len(problem.train_tapes['demands']), n_horizon=horizon,
                    llm_model=model_name, llm_api_key='injected-client-no-key', llm_api_endpoint='injected-client',
                    ec_pop_size=population_size, ec_n_pop=generations, ec_operators=['m2'], ec_m=2,
                    exp_n_proc=1, exp_use_continue=True, exp_create_initial=False,
                    exp_continue_path=str(output/'initial_pool.json'), exp_output_path=str(output),
                    external_optimizer='scipy', iter_opt=optimizer_maxiter, param_num=max_opt_params,
                    param_loc='default', repeat=repeat, filename='training_progress',
                    data_summary='processed', algo_performance='processed', prompt_version='v2',
                    prompt_with_explanations=False)
    paras.eva_timeout = float(evaluation_timeout)
    seed_path = output/'initial_pool.json'
    if not seed_path.exists():
        _atomic(seed_path, [{'algorithm': 'Base-stock seed using the training sample mean.',
                            'code': _seed_code(problem), 'objective': None, 'other_inf': None}])
    patches = [(framework['evolution'], 'InterfaceLLM', Gateway),
               (framework['interface'], 'Evolution', AdaptedEvolution),
               (framework['eoh'], 'InterfaceEC', AdaptedInterface),
               (framework['analyzer'], 'InventoryAnalyzer', TrainingAnalyzer)]
    old_values = [(module, name, getattr(module, name)) for module, name, _ in patches]
    try:
        for module, name, value in patches:
            setattr(module, name, value)
        search = AdaptedEOH(paras, problem, framework['selection'], framework['management'])
        search.run()
        best_path = output/'pops_best'/f'population_generation_{generations}.json'
        best = _read(best_path)
        if not best.get('code') or best.get('objective') is None:
            raise RuntimeError('Evolution produced no valid training-selected policy')
        # Verify and freeze the actual code once, independent of optimizer auxiliary traces.
        final = problem.evaluate(best['code'])
        if not math.isclose(float(best['objective']), final['avg'], rel_tol=1e-8, abs_tol=1e-4):
            raise ValueError('Final code training objective differs from selected record')
        (output/'policy.py').write_text(best['code'])
        records = [_read(path) for path in sorted((output/'candidates').glob('*.json.gz'))]
        answer = {'status': 'completed', 'best_code_path': str(output/'policy.py'),
                  'code_sha256': hashlib.sha256(best['code'].encode()).hexdigest(),
                  'best_train_cost': final['avg'], 'algorithm': best.get('algorithm', ''),
                  'checkpoint_path': str(output/'checkpoints'/f'g{generations:03d}.json.gz'),
                  'model_calls': sum(r['model_requests'] for r in records),
                  'training_evaluations': problem.evaluations, 'training_cache_hits': problem.cache_hits,
                  'compiled_structures': problem.compilations, 'optimizer': identity['optimizer'],
                  'optimizer_maxiter': optimizer_maxiter, 'test_evaluated': False}
        _atomic(output/'result.json', answer)
        return answer
    finally:
        problem.close()
        for module, name, value in reversed(old_values):
            setattr(module, name, value)
