import re
import numpy as np
import json
from scipy.optimize import minimize
from typing import Dict, List, Callable, Optional, Tuple, Any
import concurrent.futures
import logging
import ast
import traceback
from dataclasses import dataclass

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


class ScipyOptimizer:
    def __init__(self, interface_eval, max_iter=30, timeout: float = 30.0):
        self.interface_eval = interface_eval
        self.timeout = timeout
        self.history = []
        self.max_iter = max_iter

    def _replace_parameters(self, code: str, param_values: Dict[str, float]) -> Tuple[str, Dict[str, Tuple[int, str]]]:
        lines = code.split('\n')
        param_locations = {}
        param_found = {p: False for p in param_values.keys()}

        for i, line in enumerate(lines):
            # Get leading whitespace (indentation) of current line
            leading_whitespace = line[:len(line) - len(line.lstrip())]

            # Check if line has OPT_PARAM comment to preserve
            opt_param_comment = None
            if "OPT_PARAM:" in line:
                try:
                    # Extract the OPT_PARAM comment
                    comment_start = line.index("OPT_PARAM:")
                    param_str = line[comment_start + len("OPT_PARAM:"):].strip()
                    # Replace single quotes with double quotes for JSON parsing
                    param_str = param_str.replace("'", '"')
                    param_config = json.loads(param_str)
                    opt_param_comment = param_config
                except:
                    pass

            # Try AST parsing method
            try:
                node = ast.parse(line).body[0]
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id in param_values:
                            # Found parameter assignment line
                            param = target.id
                            new_value = param_values[param]

                            # Preserve OPT_PARAM format if it exists
                            if opt_param_comment:
                                opt_param_comment['initial'] = new_value
                                new_line = f"{leading_whitespace}{param} = {new_value}  # OPT_PARAM: {json.dumps(opt_param_comment)}"
                            else:
                                new_line = f"{leading_whitespace}{param} = {new_value}  # Optimized"

                            lines[i] = new_line
                            param_locations[param] = (i + 1, new_line)
                            param_found[param] = True
            except (SyntaxError, IndexError):
                # AST parsing failed, use regex method while preserving indentation
                for param in param_values:
                    if not param_found[param]:
                        # Match param = value pattern, keeping original indentation
                        match = re.match(fr"^(\s*){param}\s*=\s*([^#\n]+)", line)
                        if match:
                            existing_indent = match.group(1)  # Capture original indentation
                            new_value = param_values[param]

                            # Preserve OPT_PARAM format if it exists
                            if opt_param_comment:
                                opt_param_comment['initial'] = new_value
                                new_line = f"{existing_indent}{param} = {new_value}  # OPT_PARAM: {json.dumps(opt_param_comment)}"
                            else:
                                new_line = f"{existing_indent}{param} = {new_value}  # Optimized"

                            lines[i] = new_line
                            param_locations[param] = (i + 1, new_line)
                            param_found[param] = True

        return '\n'.join(lines), param_locations

    def _evaluate_code(self, modified_code: str,
                       executor: Optional[concurrent.futures.ThreadPoolExecutor] = None):
        """Evaluate code and handle potential errors"""
        try:
            if executor:
                future = executor.submit(self.interface_eval.evaluate, modified_code)
                result = future.result(timeout=self.timeout)
            else:
                result = self.interface_eval.evaluate(modified_code)

            # if not isinstance(result, (int, float)):
            #     raise ValueError(f"Evaluation function should return a number, got {type(result)}")

            return result

        except concurrent.futures.TimeoutError:
            error_msg = f"Evaluation timed out after {self.timeout} seconds"
            logger.error(error_msg)
            raise RuntimeError
            # raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Evaluation failed: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            raise RuntimeError
            # raise RuntimeError(error_msg)

    def optimize(
            self,
            original_code: str,
            opt_params: Dict[str, Dict[str, float]],
            param_vars: List[str],
            executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
    ) -> OptimizationResult:
        """
        Improved optimization method with detailed error handling

        Args:
            original_code: Python code containing optimizable parameters
            opt_params: {"param1": {"initial": 1.0, "min": 0.1, "max": 2.0}, ...}
            param_vars: List of parameter names to optimize
            executor: Optional thread pool executor

        Returns:
            OptimizationResult: Object containing optimization results and detailed error information
        """
        self.opt_params = opt_params
        for param in param_vars:
            if opt_params[param]["type"] == 'int':
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

        try:
            # 1. Sanity check: skip

            # 2. Prepare optimization variables
            initial_values = [opt_params[p]['initial'] for p in param_vars]
            bounds = [(opt_params[p]['min'], opt_params[p]['max']) for p in param_vars]

            # 3. Define objective function
            def objective(x):
                try:
                    # Create parameter dictionary
                    current_params = dict(zip(param_vars, x))
                    current_params = self.data_type(current_params)
                    # Replace parameters and record locations
                    modified_code, locations = self._replace_parameters(original_code, current_params)
                    # Evaluate code
                    fitness = self._evaluate_code(modified_code, executor)
                    # Record history
                    history_entry = {
                        'params': current_params.copy(),
                        'fitness': fitness['avg'],
                        'test_objective': fitness['test_obj'],
                        'lower': fitness['lower'],
                        'upper': fitness['upper'],
                        'trajectory': fitness['trajectory'],
                        'cost_matrix': fitness['cost_matrix'],
                        'order_matrix': fitness['order_matrix'],
                        'code': modified_code,
                        'locations': locations
                    }
                    self.history.append(history_entry)
                    result.history.append(history_entry)

                    return fitness['avg']

                except Exception as e:
                    error_msg = f"Objective function failed at parameters {current_params}: {str(e)}"
                    logger.error(error_msg)
                    result.error = error_msg
                    result.error_location = f"Parameter values: {current_params}"
                    raise

            # 4. Run optimization
            opt_result = minimize(
                objective,
                initial_values,
                bounds=bounds,
                method='L-BFGS-B',
                options={
                    'maxiter': self.max_iter,
                    'disp': True,
                    'eps': 0.1,  # Larger epsilon for numerical gradients (default is ~1e-8)
                    'ftol': 1e-6,  # Function tolerance
                    'gtol': 1e-4   # Gradient tolerance (relax from default 1e-5)
                }
            )

            # 5. Process optimization results
            # Sort history to find best result
            result.history = sorted(result.history, key=lambda x: x['fitness'], reverse=True)

            if not opt_result.success and result.history:
                # Optimization didn't converge properly, use best from history
                logger.warning(f"Optimization incomplete: {opt_result.message}")
                logger.info(f"Using best result from {len(result.history)} evaluations")
                best_partial = result.history[-1]  # Best (lowest fitness) is last

                result.optimized_code = best_partial['code']
                result.optimized_params = best_partial['params']
                result.optimized_fitness = float(best_partial['fitness'])
                result.optimized_test_fitness = best_partial['test_objective']
                result.optimized_lower = best_partial['lower']
                result.optimized_upper = best_partial['upper']
                result.optimized_trajectory = best_partial['trajectory']
                result.optimized_cost_matrix = best_partial['cost_matrix']
                result.optimized_order_matrix = best_partial['order_matrix']
                result.success = True  # We have a valid result
                result.error = opt_result.message
                result.error_location = f"Using best from history instead of final: {best_partial['params']}"
                logger.info(f"Best partial fitness: {result.optimized_fitness}")
            else:
                # Optimization succeeded or no history available, use scipy's result
                raw_optimized_params = dict(zip(param_vars, opt_result.x))
                optimized_params = self.data_type(raw_optimized_params)
                optimized_code, _ = self._replace_parameters(original_code, optimized_params)

                result.optimized_code = optimized_code
                result.optimized_params = optimized_params
                result.optimized_fitness = float(opt_result.fun)
                result.optimized_test_fitness = result.history[-1]['test_objective']
                result.optimized_lower = result.history[-1]['lower']
                result.optimized_upper = result.history[-1]['upper']
                result.optimized_trajectory = result.history[-1]['trajectory']
                result.optimized_cost_matrix = result.history[-1]['cost_matrix']
                result.optimized_order_matrix = result.history[-1]['order_matrix']
                result.success = opt_result.success

                if not opt_result.success:
                    result.error = opt_result.message
                    result.error_location = f"Final parameters: {optimized_params}"

        except Exception as e:
            result.error = str(e)
            result.error_location = traceback.format_exc()
            logger.error(f"Optimization failed: {result.error}")

            # Use best partial result if any evaluations succeeded
            if result.history:
                logger.info(f"Using best partial result from {len(result.history)} evaluations")
                # Sort history by fitness (descending), so best (lowest) is last
                result.history = sorted(result.history, key=lambda x: x['fitness'], reverse=True)
                best_partial = result.history[-1]  # Best (lowest fitness) is last

                result.optimized_code = best_partial['code']
                result.optimized_params = best_partial['params']
                result.optimized_fitness = float(best_partial['fitness'])
                result.optimized_test_fitness = best_partial['test_objective']
                result.optimized_lower = best_partial['lower']
                result.optimized_upper = best_partial['upper']
                result.optimized_trajectory = best_partial['trajectory']
                result.optimized_cost_matrix = best_partial['cost_matrix']
                result.optimized_order_matrix = best_partial['order_matrix']
                result.success = True  # Mark as success since we have a valid result
                logger.info(f"Best partial fitness: {result.optimized_fitness}")

        return result

    def data_type(self, raw_optimized_params):
        optimized_params = {}
        for param, value in raw_optimized_params.items():  # raw_optimized_params contains raw optimization results
            param_config = self.opt_params.get(param, {})
            param_type = param_config.get("type", 'float')  # Default to float

            if param_type == 'int':
                optimized_params[param] = int(round(value))  # Round to nearest integer
            else:
                optimized_params[param] = value  # Keep as float
        return optimized_params