import re
import ast
import json
import traceback
import concurrent.futures
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from scipy.optimize import minimize


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    optimized_code: str
    optimized_params: Dict[str, float]
    optimized_fitness: float
    optimized_test_fitness: float
    optimized_lower: float
    optimized_upper: float
    optimized_trajectory: List[float]
    optimized_cost_matrix: List[float]
    optimized_order_matrix: List[float]
    success: bool
    error: Optional[str] = None
    error_location: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None


class _EarlyStop(Exception):
    """Internal exception to stop SciPy minimize early based on evaluation budget."""
    pass


class ScipyOptimizer:
    """
    Plan 1 (directly replace your old code):

    - Add max_evals hard cap to avoid extremely long optimization runs
    - Cache repeated evaluations (common with rounding / line-search / integer params)
    - Never propagate exceptions/NaNs into SciPy (return finite penalty instead)
    - Improve timeout/error handling
    - Track best result incrementally (avoid sorting for selection)
    - Speed up parameter replacement (regex-based, no per-line AST parse)
    """

    def __init__(
        self,
        interface_eval,
        max_iter: int = 30,
        timeout: float = 10.0,
        *,
        max_evals: Optional[int] = 300,
        penalty: float = 1e18,
        cache_round_decimals: int = 10,
        lbfgsb_eps: float = 1e-2,
        lbfgsb_maxls: int = 10,
        ftol: float = 1e-6,
        gtol: float = 1e-4,
        disp: bool = True
    ):
        self.interface_eval = interface_eval
        self.timeout = timeout
        self.history: List[Dict[str, Any]] = []
        self.max_iter = max_iter

        # Plan-1 controls
        self.max_evals = max_evals
        self.penalty = float(penalty)
        self.cache_round_decimals = int(cache_round_decimals)

        # L-BFGS-B tuning
        self.lbfgsb_eps = float(lbfgsb_eps)
        self.lbfgsb_maxls = int(lbfgsb_maxls)
        self.ftol = float(ftol)
        self.gtol = float(gtol)
        self.disp = bool(disp)

        # Internal: regex cache for parameter replacement
        self._pattern_key: Optional[Tuple[str, ...]] = None
        self._param_patterns: Dict[str, re.Pattern] = {}
        self._current_param_vars: List[str] = []

        # Provided at optimize() time
        self.opt_params: Dict[str, Dict[str, float]] = {}

    def _get_param_patterns(self, param_vars: List[str]) -> Dict[str, re.Pattern]:
        key = tuple(param_vars)
        if self._pattern_key != key:
            self._pattern_key = key
            self._param_patterns = {
                p: re.compile(rf"^(\s*){re.escape(p)}\s*=\s*([^#\n]+)")
                for p in param_vars
            }
        return self._param_patterns

    def _parse_opt_param_comment(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse OPT_PARAM JSON/Python-dict comment if present."""
        if "OPT_PARAM:" not in line:
            return None
        try:
            comment_start = line.index("OPT_PARAM:")
            param_str = line[comment_start + len("OPT_PARAM:"):].strip()

            # Try JSON first
            try:
                param_str_json = param_str.replace("'", '"')
                return json.loads(param_str_json)
            except Exception:
                # Fallback to Python literal dict
                return ast.literal_eval(param_str)
        except Exception:
            return None

    def _replace_parameters(
        self,
        code: str,
        param_values: Dict[str, float]
    ) -> Tuple[str, Dict[str, Tuple[int, str]]]:
        """
        Fast parameter replacement (regex-based).
        Keeps indentation and preserves OPT_PARAM comment when available.
        """
        lines = code.split('\n')
        param_locations: Dict[str, Tuple[int, str]] = {}
        param_found = {p: False for p in param_values.keys()}

        param_vars = self._current_param_vars or list(param_values.keys())
        patterns = self._get_param_patterns(param_vars)

        for i, line in enumerate(lines):
            if '=' not in line:
                continue

            opt_param_comment = self._parse_opt_param_comment(line)

            for param in param_vars:
                if param not in param_values or param_found.get(param, False):
                    continue

                m = patterns[param].match(line)
                if not m:
                    continue

                indent = m.group(1)
                new_value = param_values[param]

                if opt_param_comment is not None and isinstance(opt_param_comment, dict):
                    cfg = dict(opt_param_comment)
                    cfg['initial'] = new_value
                    new_line = f"{indent}{param} = {new_value}  # OPT_PARAM: {json.dumps(cfg)}"
                else:
                    new_line = f"{indent}{param} = {new_value}  # Optimized"

                lines[i] = new_line
                param_locations[param] = (i + 1, new_line)
                param_found[param] = True

            if all(param_found.values()):
                break

        return '\n'.join(lines), param_locations

    def _evaluate_code(
        self,
        modified_code: str,
        executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
    ):
        """Evaluate code with robust timeout/error handling."""
        try:
            if executor:
                future = executor.submit(self.interface_eval.evaluate, modified_code)
                try:
                    return future.result(timeout=self.timeout)
                except concurrent.futures.TimeoutError as e:
                    try:
                        future.cancel()
                    except Exception:
                        pass
                    msg = f"Evaluation timed out after {self.timeout} seconds"
                    logger.error(msg)
                    raise RuntimeError(msg) from e
            else:
                return self.interface_eval.evaluate(modified_code)

        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            msg = f"Evaluation failed: {str(e)}\n{traceback.format_exc()}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    def data_type(self, raw_optimized_params: Dict[str, Any]) -> Dict[str, float]:
        """Convert optimization vector into configured types (int/float)."""
        optimized_params: Dict[str, float] = {}
        for param, value in raw_optimized_params.items():
            param_config = self.opt_params.get(param, {})
            param_type = param_config.get("type", 'float')

            if param_type == 'int':
                optimized_params[param] = int(round(float(value)))
            else:
                optimized_params[param] = float(value)
        return optimized_params

    def optimize(
        self,
        original_code: str,
        opt_params: Dict[str, Dict[str, float]],
        param_vars: List[str],
        executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
    ) -> OptimizationResult:
        """
        Run optimization with evaluation budget/caching and safe failure handling.
        """
        self.opt_params = opt_params
        self._current_param_vars = list(param_vars)
        self.history = []  # reset per run

        # Keep your original behavior: cast int params for bounds/initial
        for param in param_vars:
            if opt_params[param].get("type") == 'int':
                opt_params[param]["initial"] = int(opt_params[param]["initial"])
                opt_params[param]["min"] = int(opt_params[param]["min"])
                opt_params[param]["max"] = int(opt_params[param]["max"])

        result = OptimizationResult(
            optimized_code=original_code,
            optimized_params={},
            optimized_fitness=float('inf'),
            optimized_test_fitness=float('inf'),
            optimized_lower=float('inf'),
            optimized_upper=float('inf'),
            optimized_trajectory=[],
            optimized_cost_matrix=[],
            optimized_order_matrix=[],
            success=False,
            history=[]
        )

        # Prepare variables
        initial_values = [opt_params[p]['initial'] for p in param_vars]
        bounds = [(opt_params[p]['min'], opt_params[p]['max']) for p in param_vars]

        # Eval cache: key -> objective value
        eval_cache: Dict[Tuple[Any, ...], float] = {}
        expensive_evals = 0
        best_entry: Optional[Dict[str, Any]] = None

        def make_key(params: Dict[str, float]) -> Tuple[Any, ...]:
            key_parts: List[Any] = []
            for p in param_vars:
                if self.opt_params.get(p, {}).get("type") == "int":
                    key_parts.append(int(params[p]))
                else:
                    key_parts.append(round(float(params[p]), self.cache_round_decimals))
            return tuple(key_parts)

        def objective(x):
            nonlocal expensive_evals, best_entry

            current_params = self.data_type(dict(zip(param_vars, x)))
            key = make_key(current_params)

            # Cache hit
            if key in eval_cache:
                return eval_cache[key]

            # Budget check (budget counts real evaluations, not cache hits)
            if self.max_evals is not None and expensive_evals >= self.max_evals:
                raise _EarlyStop(f"Reached max_evals={self.max_evals}")

            try:
                modified_code, locations = self._replace_parameters(original_code, current_params)
                fitness = self._evaluate_code(modified_code, executor)

                fval = float(fitness["avg"])
                if not np.isfinite(fval):
                    raise ValueError(f"Non-finite fitness['avg']: {fval}")

                history_entry = {
                    'params': current_params.copy(),
                    'fitness': fval,
                    'test_objective': fitness.get('test_obj'),
                    'lower': fitness.get('lower'),
                    'upper': fitness.get('upper'),
                    'trajectory': fitness.get('trajectory'),
                    'cost_matrix': fitness.get('cost_matrix'),
                    'order_matrix': fitness.get('order_matrix'),
                    'code': modified_code,
                    'locations': locations
                }

                self.history.append(history_entry)
                result.history.append(history_entry)

                expensive_evals += 1
                eval_cache[key] = fval

                if best_entry is None or fval < float(best_entry['fitness']):
                    best_entry = history_entry

                return fval

            except Exception as e:
                # Do NOT raise into SciPy; return penalty to keep optimizer stable
                msg = f"Objective failed at params={current_params}: {e}"
                logger.warning(msg)

                expensive_evals += 1
                eval_cache[key] = self.penalty

                result.error = msg
                result.error_location = f"Parameter values: {current_params}"
                return self.penalty

        # Run SciPy minimize
        opt_result = None
        early_stop_msg = None

        options = {
            'maxiter': self.max_iter,
            'disp': self.disp,
            'eps': self.lbfgsb_eps,
            'ftol': self.ftol,
            'gtol': self.gtol,
            'maxls': self.lbfgsb_maxls,
        }
        if self.max_evals is not None:
            options['maxfun'] = int(self.max_evals)

        try:
            opt_result = minimize(
                objective,
                initial_values,
                bounds=bounds,
                method='L-BFGS-B',
                options=options
            )
        except _EarlyStop as e:
            early_stop_msg = str(e)
            logger.warning(f"Early stop: {early_stop_msg}")
        except Exception as e:
            result.error = str(e)
            result.error_location = traceback.format_exc()
            logger.error(f"Optimization failed: {result.error}")

        # Use best evaluated result (most robust)
        if best_entry is not None:
            result.optimized_code = best_entry['code']
            result.optimized_params = best_entry['params']
            result.optimized_fitness = float(best_entry['fitness'])

            # Optional fields
            test_obj = best_entry.get('test_objective')
            try:
                result.optimized_test_fitness = float(test_obj) if test_obj is not None else float('inf')
            except Exception:
                result.optimized_test_fitness = test_obj

            result.optimized_lower = best_entry.get('lower', float('inf'))
            result.optimized_upper = best_entry.get('upper', float('inf'))
            result.optimized_trajectory = best_entry.get('trajectory', []) or []
            result.optimized_cost_matrix = best_entry.get('cost_matrix', []) or []
            result.optimized_order_matrix = best_entry.get('order_matrix', []) or []

            result.success = True

            # Provide helpful messages if scipy didn't "success" or we early-stopped
            if early_stop_msg:
                result.error = early_stop_msg
                result.error_location = f"Used best result from {len(result.history)} evaluations (early stop)."
            elif opt_result is not None and not bool(getattr(opt_result, "success", False)):
                result.error = str(getattr(opt_result, "message", "Optimization incomplete"))
                result.error_location = f"Used best result from {len(result.history)} evaluations (scipy incomplete)."

            logger.info(f"Using best result from {len(result.history)} evaluations")
            logger.info(f"Best partial fitness: {result.optimized_fitness}")

        else:
            result.success = False
            if early_stop_msg:
                result.error = early_stop_msg
            if result.error is None:
                result.error = "No successful evaluations (all runs failed or timed out)."
            if result.error_location is None:
                result.error_location = "Check evaluate() timeouts/exceptions."

        # Keep your old behavior: sort history by fitness descending (best is last)
        if result.history:
            try:
                result.history = sorted(result.history, key=lambda h: h['fitness'], reverse=True)
            except Exception:
                pass

        return result
