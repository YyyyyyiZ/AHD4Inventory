import re
import numpy as np
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
    success: bool
    error: Optional[str] = None
    error_location: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None


class ExternalOptimizer:
    def __init__(self, interface_eval, timeout: float = 10.0):
        self.interface_eval = interface_eval
        self.timeout = timeout
        self.history = []

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
                       executor: Optional[concurrent.futures.ThreadPoolExecutor] = None) -> float:
        """Evaluate code and handle potential errors"""
        try:
            if executor:
                future = executor.submit(self.interface_eval.evaluate, modified_code)
                result = future.result(timeout=self.timeout)
            else:
                result = self.interface_eval.evaluate(modified_code)

            if not isinstance(result, (int, float)):
                raise ValueError(f"Evaluation function should return a number, got {type(result)}")

            return float(result)

        except concurrent.futures.TimeoutError:
            error_msg = f"Evaluation timed out after {self.timeout} seconds"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Evaluation failed: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

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
                        'fitness': fitness,
                        'code': modified_code,
                        'locations': locations
                    }
                    self.history.append(history_entry)
                    result.history.append(history_entry)

                    return fitness

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
                options={'maxiter': 20, 'disp': True}
            )

            # 5. Generate final optimized code
            raw_optimized_params = dict(zip(param_vars, opt_result.x))

            optimized_params = self.data_type(raw_optimized_params)

            optimized_code, _ = self._replace_parameters(original_code, optimized_params)

            # Update results
            result.optimized_code = optimized_code
            result.optimized_params = optimized_params
            result.optimized_fitness = float(opt_result.fun)
            result.success = opt_result.success

            if not opt_result.success:
                result.error = opt_result.message
                result.error_location = f"Final parameters: {optimized_params}"

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