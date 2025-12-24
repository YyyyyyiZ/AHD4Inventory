import numpy as np
import time
from .eoh_evolution import Evolution
import warnings
from joblib import Parallel, delayed
from .evaluator_accelerate import add_numba_decorator
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import re
import concurrent.futures


class InterfaceEC:
    def __init__(self, pop_size, m, api_endpoint, api_key, llm_model, llm_use_local, llm_local_url, debug_mode,
                 interface_prob, analyzer, external_optimizer, max_iter, param_loc,
                 exp_output_path, select, n_p, timeout, use_numba, **kwargs):

        # LLM settings
        self.pop_size = pop_size
        self.interface_eval = interface_prob
        prompts = interface_prob.prompts
        self.evol = Evolution(api_endpoint, api_key, llm_model, llm_use_local, llm_local_url, debug_mode, prompts,
                              analyzer, external_optimizer, param_loc, exp_output_path,
                              **kwargs)
        self.m = m
        self.debug = debug_mode

        if not self.debug:
            warnings.filterwarnings("ignore")

        self.select = select
        self.n_p = n_p

        self.timeout = timeout
        self.use_numba = use_numba

        self.external_optimizer = external_optimizer
        self.max_iter = max_iter

    def code2file(self, code):
        with open("./ael_alg.py", "w") as file:
            # Write the code to the file
            file.write(code)
        return

    def add2pop(self, population, offspring):
        for i, ind in enumerate(population):
            if ind['objective'] == offspring['objective']:
                # Same performance found - replace old individual with fresh response
                if self.debug:
                    print(f"Same objective found, updating with fresh response (obj: {offspring['objective']})")
                population[i] = offspring  # Replace old individual with new one
                return True
        # No duplicate performance found, add new individual
        population.append(offspring)
        return True

    def check_duplicate(self, population, code):
        for ind in population:
            if code == ind['code']:
                return True
        return False

    def population_init_obj(self, pop, n_p):
        fitness = Parallel(n_jobs=n_p)(delayed(self.interface_eval.evaluate)(seed['code']) for seed in pop)
        for i in range(len(pop)):
            obj = np.array(fitness[i]['avg'])
            pop[i]['objective'] = np.round(obj, 5)
            pop[i]['test_objective'] = np.round(np.array(fitness[i]['test_obj']), 5)
            pop[i]['lower'] = np.round(np.array(fitness[i]['lower']), 5)
            pop[i]['upper'] = np.round(np.array(fitness[i]['upper']), 5)
            pop[i]['trajectory'] = fitness[i]['trajectory']
            pop[i]['cost_matrix'] = fitness[i]['cost_matrix']
            pop[i]['order_matrix'] = fitness[i]['order_matrix']
        return pop

    def optimize_individual(self, individual):
        """Optimize a single individual if it has parameters and external optimizer is enabled."""
        if self.external_optimizer is None:
            return individual

        # Extract opt_params from code if not already present
        if 'opt_params' not in individual or len(individual.get('opt_params', {})) == 0:
            individual['opt_params'] = self._extract_opt_params_from_code(individual['code'])

        # Check if individual has opt_params after extraction
        if len(individual.get('opt_params', {})) == 0:
            if self.debug:
                print("Individual has no parameters to optimize, skipping.")
            return individual

        # Determine which optimizer to use
        if self.external_optimizer == 'scipy':
            from .external_scipy import ScipyOptimizer as ExternalOptimizer
        elif self.external_optimizer == 'ng':
            from .external_nevergrad import NGOptimizer as ExternalOptimizer
        elif self.external_optimizer == 'deap':
            from .external_deap import DEAPOptimizer as ExternalOptimizer
        else:
            return individual

        # Store original performance for comparison
        original_objective = individual.get('objective', float('inf'))

        try:
            optimizer = ExternalOptimizer(
                interface_eval=self.interface_eval,
                max_iter=self.max_iter,
                timeout=self.timeout
            )

            opt_result = optimizer.optimize(
                original_code=individual['code'],
                opt_params=individual['opt_params'],
                param_vars=list(individual['opt_params'].keys()),
                executor=concurrent.futures.ThreadPoolExecutor()
            )

            # Compare optimized result with original, use better one
            if opt_result.optimized_fitness < original_objective:
                # Optimization improved performance
                individual.update({
                    'code': opt_result.optimized_code,
                    'objective': np.round(opt_result.optimized_fitness, 5),
                    'test_objective': np.round(opt_result.optimized_test_fitness, 5),
                    'lower': np.round(opt_result.optimized_lower, 5),
                    'upper': np.round(opt_result.optimized_upper, 5),
                    'trajectory': opt_result.optimized_trajectory,
                    'cost_matrix': opt_result.optimized_cost_matrix,
                    'order_matrix': opt_result.optimized_order_matrix,
                    'opt_params': opt_result.optimized_params
                })

                if self.debug:
                    print(f"Optimized individual improved: {original_objective} -> {opt_result.optimized_fitness}")
            else:
                # Original was better, keep it
                if self.debug:
                    print(f"Original individual was better: {original_objective} vs {opt_result.optimized_fitness}")

        except Exception as e:
            if self.debug:
                print(f"Failed to optimize individual: {e}")
            # Keep original individual as-is

        return individual

    def _extract_opt_params_from_code(self, code):
        """Extract optimizable parameters from code with OPT_PARAM comments."""
        import json
        opt_params = {}

        for line in code.split('\n'):
            if "OPT_PARAM:" in line:
                # Extract parameter name
                match = re.match(r'^\s*(\w+)\s*=', line)
                if match:
                    param_name = match.group(1)
                    # Extract parameter configuration
                    param_str = line.split("OPT_PARAM:")[1].strip()
                    param_str = param_str.replace("'", '"')
                    try:
                        param_config = json.loads(param_str)
                        opt_params[param_name] = param_config
                    except:
                        if self.debug:
                            print(f"Failed to parse OPT_PARAM for {param_name}")

        return opt_params

    def population_generation(self):
        n_create = 1
        population = []
        for i in range(n_create):
            _, pop = self.get_algorithm([], 'i1')
            for p in pop:
                population.append(p)
        return population

    def population_generation_seed(self, seeds, n_p):

        population = []

        fitness = Parallel(n_jobs=n_p)(delayed(self.interface_eval.evaluate)(seed['code']) for seed in seeds)

        for i in range(len(seeds)):
            try:
                seed_alg = {
                    'algorithm': seeds[i]['algorithm'],
                    'code': seeds[i]['code'],
                    'objective': None,
                    'test_objective': None,
                    'lower': None,
                    'upper': None,
                    'trajectory': None,
                    'cost_matrix': None,
                    'order_matrix': None,
                    'other_inf': None
                }

                obj = np.array(fitness[i]['avg'])
                seed_alg['objective'] = np.round(obj, 5)
                seed_alg['test_objective'] = np.round(np.array(fitness[i]['test_obj']), 5)
                seed_alg['lower'] = np.round(np.array(fitness[i]['lower']), 5)
                seed_alg['upper'] = np.round(np.array(fitness[i]['upper']), 5)
                seed_alg['trajectory'] = fitness[i]['trajectory']
                seed_alg['cost_matrix'] = fitness[i]['cost_matrix']
                seed_alg['order_matrix'] = fitness[i]['order_matrix']
                population.append(seed_alg)

            except Exception as e:
                print("Error in seed algorithm")
                exit()

        print("Initiliazation finished! Get " + str(len(seeds)) + " seed algorithms")

        return population

    def _get_alg(self, pop, operator):
        offspring = {
            'algorithm': None,
            'code': None,
            'opt_params': {},
            'cost': None,
            'objective': None,
            'test_objective': None,
            'lower': None,
            'upper': None,
            'trajectory': None,
            'cost_matrix': None,
            'order_matrix': None,
            'other_inf': None
        }
        if operator == "i1":
            parents = None
            [offspring['code'], offspring['algorithm'], offspring['opt_params'], offspring['cost']] = self.evol.i1()
            # print("off:", offspring)
        elif operator == "e1":
            parents = self.select.parent_selection(pop, self.m)
            [offspring['code'], offspring['algorithm'], offspring['opt_params'], offspring['cost']] = self.evol.e1(
                parents)
        elif operator == "e2":
            parents = self.select.parent_selection(pop, self.m)
            [offspring['code'], offspring['algorithm'], offspring['opt_params'], offspring['cost']] = self.evol.e2(
                parents)
        elif operator == "m1":
            parents = self.select.parent_selection(pop, 1)
            [offspring['code'], offspring['algorithm'], offspring['opt_params'], offspring['cost']] = self.evol.m1(
                parents[0])
        elif operator == "m2":
            parents = self.select.parent_selection(pop, 1)
            [offspring['code'], offspring['algorithm'], offspring['opt_params'], offspring['cost']] = self.evol.m2(
                parents[0])
        elif operator == "m2plural":
            parents = self.select.parent_selection(pop, self.m)
            [offspring['code'], offspring['algorithm'], offspring['opt_params'], offspring['cost']] = self.evol.m2plural(
                parents)
        elif operator == "temp":
            parents = self.select.parent_selection(pop, self.m)
            [offspring['code'], offspring['algorithm'], offspring['opt_params'], offspring['cost']] = self.evol.op_temp(
                parents)
        elif operator == "m3":
            parents = self.select.parent_selection(pop, 1)
            [offspring['code'], offspring['algorithm'], offspring['opt_params'], offspring['cost']] = self.evol.m3(
                parents[0])
        else:
            print(f"Evolution operator [{operator}] has not been implemented ! \n")

        return parents, offspring

    def get_offspring(self, pop, operator, n_pop):
        try:
            p, offspring = self._get_alg(pop, operator)

            if self.use_numba:
                # Regular expression pattern to match function definitions
                pattern = r"def\s+(\w+)\s*\(.*\):"
                # Search for function definitions in the code
                match = re.search(pattern, offspring['code'])
                function_name = match.group(1)
                code = add_numba_decorator(program=offspring['code'], function_name=function_name)
            else:
                code = offspring['code']

            n_retry = 1
            while self.check_duplicate(pop, offspring['code']):
                n_retry += 1
                if self.debug:
                    print("duplicated code, wait 1 second and retrying ... ")
                p, offspring = self._get_alg(pop, operator)
                if self.use_numba:
                    # Regular expression pattern to match function definitions
                    pattern = r"def\s+(\w+)\s*\(.*\):"
                    # Search for function definitions in the code
                    match = re.search(pattern, offspring['code'])
                    function_name = match.group(1)
                    code = add_numba_decorator(program=offspring['code'], function_name=function_name)
                else:
                    code = offspring['code']

                if n_retry > 1:
                    break
            # print("offspring:", offspring)

            ext = False
            if self.external_optimizer == 'scipy' and len(offspring['opt_params']) != 0:
                from .external_scipy import ScipyOptimizer as ExternalOptimizer
                ext = True
            elif self.external_optimizer == 'ng':
                from .external_nevergrad import NGOptimizer as ExternalOptimizer
                ext = True
            elif self.external_optimizer == 'deap':
                from .external_deap import DEAPOptimizer as ExternalOptimizer
                ext = True
            # if ext:
            # print(n_pop)
            # if ext and n_pop==9:
            if ext:
                try:
                    # First evaluate original code for comparison
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self.interface_eval.evaluate, code)
                        original_fitness = future.result(timeout=self.timeout)
                        future.cancel()

                    # print(f"Original parameters: {offspring['opt_params']}")
                    optimizer = ExternalOptimizer(
                        interface_eval=self.interface_eval,
                        max_iter=self.max_iter,
                        timeout=self.timeout
                    )

                    opt_result = optimizer.optimize(
                        original_code=code,
                        opt_params=offspring['opt_params'],
                        param_vars=list(offspring['opt_params'].keys()),
                        executor=concurrent.futures.ThreadPoolExecutor()
                    )

                    # Compare optimized vs original, use better one
                    if opt_result.optimized_fitness < original_fitness['avg']:
                        # Use optimized result
                        offspring.update({
                            'code': opt_result.optimized_code,
                            'objective': np.round(opt_result.optimized_fitness, 5),
                            'test_objective': np.round(opt_result.optimized_test_fitness, 5),
                            'lower': np.round(opt_result.optimized_lower, 5),
                            'upper': np.round(opt_result.optimized_upper, 5),
                            'trajectory': opt_result.optimized_trajectory,
                            'cost_matrix': opt_result.optimized_cost_matrix,
                            'order_matrix': opt_result.optimized_order_matrix,
                            'opt_params': opt_result.optimized_params
                        })
                    else:
                        # Use original result
                        offspring.update({
                            'objective': np.round(original_fitness['avg'], 5),
                            'test_objective': np.round(original_fitness['test_obj'], 5),
                            'lower': np.round(original_fitness['lower'], 5),
                            'upper': np.round(original_fitness['upper'], 5),
                            'trajectory': original_fitness['trajectory'],
                            'cost_matrix': original_fitness['cost_matrix'],
                            'order_matrix': original_fitness['order_matrix']
                        })

                    # print(f"optimized parameters: {opt_result.optimized_params}")

                except Exception as e:
                    # Both original evaluation and optimization failed, re-raise to outer handler
                    if self.debug:
                        print(f"Failed to evaluate/optimize offspring: {e}")
                    raise
            else:
                #self.code2file(offspring['code'])
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self.interface_eval.evaluate, code)
                    fitness = future.result(timeout=self.timeout)
                    offspring['objective'] = np.round(fitness['avg'], 5)
                    offspring['test_objective'] = np.round(fitness['test_obj'], 5)
                    offspring['lower'] = np.round(fitness['lower'], 5)
                    offspring['upper'] = np.round(fitness['upper'], 5)
                    offspring['trajectory'] = fitness['trajectory']
                    offspring['cost_matrix'] = fitness['cost_matrix']
                    offspring['order_matrix'] = fitness['order_matrix']
                    future.cancel()
                    # fitness = self.interface_eval.evaluate(code)


        except Exception as e:
            # print(e)
            offspring = {
                'algorithm': None,
                'code': None,
                'objective': None,
                'test_objective': None,
                'lower': None,
                'upper': None,
                'trajectory': None,
                'cost_matrix': None,
                'order_matrix': None,
                'other_inf': None
            }
            p = None
        return p, offspring

    @staticmethod
    def run_with_timeout(func, args=(), kwargs=None, timeout=None):
        if kwargs is None:
            kwargs = {}
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except TimeoutError:
                print("Parallel time out .")
                offspring = {
                    'algorithm': None,
                    'code': None,
                    'objective': None,
                    'test_objective': None,
                    'lower': None,
                    'upper': None,
                    'trajectory': None,
                    'cost_matrix': None,
                    'order_matrix': None,
                    'other_inf': None
                }
                p = None
                return p, offspring

    def get_algorithm(self, pop, operator, n_pop=1):

        # results = Parallel(n_jobs=self.n_p)(
        #     delayed(self.run_with_timeout)(
        #         self.get_offspring,
        #         args=(pop, operator, n_pop),
        #         timeout=self.timeout
        #     ) for _ in range(self.pop_size)
        # )

        results = []
        try:
            # Use configured timeout for parallel execution
            results = Parallel(n_jobs=self.n_p, timeout=self.timeout)(
                delayed(self.get_offspring)(pop, operator, n_pop) for _ in range(self.pop_size))
        except Exception as e:
            if self.debug:
                print(f"Error: {e}")
            print("Parallel execution error or timeout - continuing with partial results.")
            # If timeout, results will be empty, which is handled below

        time.sleep(10)

        out_p = []
        out_off = []

        for p, off in results:
            out_p.append(p)
            out_off.append(off)
            if self.debug:
                print(f">>> check offsprings: \n {off}")
        return out_p, out_off
