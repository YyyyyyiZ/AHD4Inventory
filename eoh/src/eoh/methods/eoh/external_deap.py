import re
import random
import numpy as np
from deap import algorithms, base, creator, tools
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
    success: bool
    error: Optional[str] = None
    error_location: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None


class DEAPOptimizer:
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

    def optimize(
            self,
            original_code: str,
            opt_params: Dict[str, Dict[str, float]],
            param_vars: List[str],
            executor: Optional[concurrent.futures.ThreadPoolExecutor] = None,
            pop_size: int = 30,
    ) -> OptimizationResult:
        """
        DEAP-based evolutionary optimization

        Args:
            original_code: Python code containing optimizable parameters
            opt_params: {"param1": {"initial": 1.0, "min": 0.1, "max": 2.0}, ...}
            param_vars: List of parameter names to optimize
            executor: Optional thread pool executor
            pop_size: Optional number of population size

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
            success=False,
            history=[]
        )

        try:
            # 1. Setup DEAP evolutionary algorithm
            creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
            creator.create("Individual", list, fitness=creator.FitnessMin)

            toolbox = base.Toolbox()

            # Register attribute generators for each parameter
            for param in param_vars:
                if opt_params[param]["type"] == "int":
                    toolbox.register(
                        f"attr_{param}",
                        random.randint,
                        opt_params[param]["min"],
                        opt_params[param]["max"]
                    )
                else:
                    toolbox.register(
                        f"attr_{param}",
                        random.uniform,
                        opt_params[param]["min"],
                        opt_params[param]["max"]
                    )

            # Initialize individual and population
            toolbox.register(
                "individual",
                tools.initCycle,
                creator.Individual,
                (getattr(toolbox, f"attr_{param}") for param in param_vars),
                n=1
            )
            toolbox.register("population", tools.initRepeat, list, toolbox.individual)

            # 2. Define evaluation function
            def evaluate(individual):
                current_params = dict(zip(param_vars, individual))
                current_params = self.data_type(current_params)

                modified_code, locations = self._replace_parameters(original_code, current_params)
                fitness = self._evaluate_code(modified_code, executor)

                history_entry = {
                    'params': current_params.copy(),
                    'fitness': fitness['avg'],
                    'test_objective': fitness['test_obj'],
                    'lower': fitness['lower'],
                    'upper': fitness['upper'],
                    'trajectory': fitness['trajectory'],
                    'code': modified_code,
                    'locations': locations
                }
                self.history.append(history_entry)
                result.history.append(history_entry)

                return (fitness['avg'],)

            toolbox.register("evaluate", evaluate)
            toolbox.register("mate", tools.cxBlend, alpha=0.5)
            toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
            toolbox.register("select", tools.selTournament, tournsize=3)

            # 3. Run evolutionary algorithm
            pop = toolbox.population(n=pop_size)
            hof = tools.HallOfFame(1)
            stats = tools.Statistics(lambda ind: ind.fitness.values[0])
            stats.register("avg", np.mean)
            stats.register("min", np.min)
            stats.register("max", np.max)

            algorithms.eaSimple(
                pop, toolbox, cxpb=0.7, mutpb=0.2, ngen=self.max_iter // pop_size,
                stats=stats, halloffame=hof, verbose=False
            )

            # 4. Extract results
            best_ind = hof[0]
            optimized_params = self.data_type(dict(zip(param_vars, best_ind)))
            optimized_code, _ = self._replace_parameters(original_code, optimized_params)

            # Find best result from history
            best_run = min(result.history, key=lambda x: x['fitness'])

            # Populate results
            result.optimized_code = optimized_code
            result.optimized_params = optimized_params
            result.optimized_fitness = float(best_run['fitness'])
            result.optimized_test_fitness = best_run['test_objective']
            result.optimized_lower = best_run['lower']
            result.optimized_upper = best_run['upper']
            result.optimized_trajectory = best_run['trajectory']
            result.success = True
            result.history = sorted(result.history, key=lambda x: x['fitness'], reverse=True)

        except Exception as e:
            result.error = str(e)
            result.error_location = traceback.format_exc()
            logger.error(f"Optimization failed: {result.error}")

        finally:
            # Clean up DEAP classes to avoid pickle issues
            if 'FitnessMin' in creator.__dict__:
                del creator.FitnessMin
            if 'Individual' in creator.__dict__:
                del creator.Individual

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