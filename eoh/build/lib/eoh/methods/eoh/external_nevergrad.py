import re
import nevergrad as ng
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


class NGOptimizer:
    def __init__(self, interface_eval, max_iter=30, timeout: float = 10.0):
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

            # Try AST parsing method
            try:
                node = ast.parse(line).body[0]
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id in param_values:
                            # Found parameter assignment line
                            param = target.id
                            new_value = param_values[param]
                            # Preserve original indentation
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
                            # Use original indentation
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
        Nevergrad-based optimization maintaining same interface as scipy version

        Args:
            original_code: Python code containing optimizable parameters
            opt_params: {"param1": {"initial": 1.0, "min": 0.1, "max": 2.0}, ...}
            param_vars: List of parameter names to optimize
            executor: Optional thread pool executor

        Returns:
            OptimizationResult: Object containing optimization results
        """
        self.opt_params = opt_params
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
            # 1. Prepare parameter space for Nevergrad
            parametrization = ng.p.Dict()
            for param in param_vars:
                if opt_params[param]["type"] == "int":
                    parametrization[param] = ng.p.Scalar(
                        init=opt_params[param]["initial"],
                        lower=opt_params[param]["min"],
                        upper=opt_params[param]["max"]
                    ).set_integer_casting()
                else:
                    parametrization[param] = ng.p.Scalar(
                        init=opt_params[param]["initial"],
                        lower=opt_params[param]["min"],
                        upper=opt_params[param]["max"]
                    )

            # 2. Define objective function (same as original)
            def objective(x):
                try:
                    current_params = self.data_type(x.value)
                    modified_code, locations = self._replace_parameters(original_code, current_params)
                    fitness = self._evaluate_code(modified_code, executor)

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
                    return float('inf')

            # 3. Run Nevergrad optimization
            optimizer = ng.optimizers.NGOpt(
                parametrization=parametrization,
                budget=self.max_iter
            )

            for _ in range(optimizer.budget):
                x = optimizer.ask()
                loss = objective(x)
                optimizer.tell(x, loss)

            # 4. Get final results
            recommendation = optimizer.provide_recommendation()
            optimized_params = self.data_type(recommendation.value)
            optimized_code, _ = self._replace_parameters(original_code, optimized_params)

            # Find best result from history
            best_run = min(result.history, key=lambda x: x['fitness'])

            # Populate results (matching original interface)
            result.optimized_code = optimized_code
            result.optimized_params = optimized_params
            result.optimized_fitness = float(best_run['fitness'])
            result.optimized_test_fitness = best_run['test_objective']
            result.optimized_lower = best_run['lower']
            result.optimized_upper = best_run['upper']
            result.optimized_trajectory = best_run['trajectory']
            result.optimized_cost_matrix = result.history[-1]['cost_matrix']
            result.optimized_order_matrix = result.history[-1]['order_matrix']
            result.success = True  # Nevergrad doesn't have success flag

        except Exception as e:
            result.error = str(e)
            result.error_location = traceback.format_exc()
            logger.error(f"Optimization failed: {result.error}")

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