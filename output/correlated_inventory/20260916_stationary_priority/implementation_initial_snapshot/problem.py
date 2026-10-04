"""Training-only evaluation adapter for the existing EOH and SciPy interfaces."""
from __future__ import annotations

from collections import OrderedDict
import hashlib
import json
from pathlib import Path
import threading
import time

import numpy as np

from .data import validate_tapes
from .fast_policy import FastPolicyWorker, prepare_policy
from .prompts import GetPrompts


class TrainingProblem:
    def __init__(self, scenario, train_tapes, *, output_dir=None, burnin=500, horizon=200,
                 evaluation_timeout=180., max_opt_params=4, python_executable=None):
        self.scenario = scenario
        self.train_tapes = validate_tapes(train_tapes, scenario)
        self.burnin, self.horizon = int(burnin), int(horizon)
        if self.burnin < 0 or self.horizon < 1 or self.burnin+self.horizon > self.train_tapes['demands'].shape[1]:
            raise ValueError("Invalid training window")
        self.prompts = GetPrompts(scenario, self.burnin, self.horizon)
        self.output_dir = Path(output_dir) if output_dir is not None else None
        self.evaluation_timeout = float(evaluation_timeout)
        self.max_opt_params, self.python_executable = int(max_opt_params), python_executable
        self._worker = None
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self.evaluations, self.cache_hits, self.compilations = 0, 0, 0
        self.context = {}

    def load_instances(self, mode='train', n_traj=None):
        """Compatibility only; asking this object for test data is an error."""
        if mode != 'train':
            raise ValueError("TrainingProblem never exposes or loads test data")
        count = len(self.train_tapes['demands']) if n_traj is None else min(int(n_traj), len(self.train_tapes['demands']))
        s = self.scenario
        return [dict(lead_time=s.max_lead_time, initial_inventory=0., holding_cost=s.holding_cost,
                     lost_sales_cost=s.lost_sales_cost,
                     demand=self.train_tapes['demands'][i, :self.burnin+self.horizon].tolist())
                for i in range(count)]

    def _get_worker(self):
        if self._worker is None:
            self._worker = FastPolicyWorker(self.train_tapes, self.scenario,
                                           burnin=self.burnin, horizon=self.horizon,
                                           timeout=max(1., self.evaluation_timeout-5.),
                                           max_opt_params=self.max_opt_params,
                                           python_executable=self.python_executable)
        return self._worker

    def evaluate(self, code_string):
        # No test result is computed. NaN satisfies old numeric field plumbing;
        # the evolution adapter removes that field from every public artifact.
        with self._lock:
            prepared = prepare_policy(code_string, self.max_opt_params)
            key = prepared['code_sha256']
            if key in self._cache:
                self.cache_hits += 1
                self._cache.move_to_end(key)
                return self._cache[key]
            started = time.monotonic()
            try:
                answer = self._get_worker().evaluate(code_string)
            except (TimeoutError, RuntimeError):
                self.close()
                raise
            self.evaluations += 1
            self.compilations += int(answer['compiled_new'])
            answer['test_obj'] = float('nan')
            self._cache[key] = answer
            if len(self._cache) > 64:
                self._cache.popitem(last=False)
            if self.output_dir is not None:
                self.output_dir.mkdir(parents=True, exist_ok=True)
                record = {**self.context, 'code_sha256': key, 'structure_sha256': answer['structure_sha256'],
                          'train_mean_cost': answer['avg'], 'opt_params': prepared['opt_params'],
                          'parameter_values': prepared['values'], 'compiled_new': answer['compiled_new'],
                          'elapsed_seconds': time.monotonic()-started,
                          'n_training_paths': len(self.train_tapes['demands']),
                          'burnin': self.burnin, 'scored_horizon': self.horizon}
                with (self.output_dir/'training_evaluations.jsonl').open('a') as f:
                    f.write(json.dumps(record, allow_nan=False)+'\n')
            return answer

    def close(self):
        with self._lock:
            if self._worker is not None:
                self._worker.close()
                self._worker = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()
