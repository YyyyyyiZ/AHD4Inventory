import numpy as np
import time
from .eoh_evolution import Evolution
import warnings
from joblib import Parallel, delayed
from .evaluator_accelerate import add_numba_decorator
import re
import concurrent.futures

class InterfaceEC():
    def __init__(self, pop_size, m, api_endpoint, api_key, llm_model,llm_use_local,llm_local_url, debug_mode,
                 interface_prob, reflect, K1, K2, external_optimizer, exp_output_path,
                 background_info, background_type, data_sep, prompt_type, select,n_p,timeout,use_numba,**kwargs):

        # LLM settings
        self.pop_size = pop_size
        self.interface_eval = interface_prob
        prompts = interface_prob.prompts
        self.evol = Evolution(api_endpoint, api_key, llm_model,llm_use_local,llm_local_url, debug_mode,prompts,
                              reflect, K1, K2, external_optimizer, exp_output_path,
                              background_info, background_type, data_sep,
                              prompt_type, **kwargs)
        self.m = m
        self.debug = debug_mode

        if not self.debug:
            warnings.filterwarnings("ignore")

        self.select = select
        self.n_p = n_p
        
        self.timeout = timeout
        self.use_numba = use_numba

        self.reflect = reflect
        self.external_optimizer = external_optimizer
        self.background_type = background_type

        
    def code2file(self,code):
        with open("./ael_alg.py", "w") as file:
        # Write the code to the file
            file.write(code)
        return 
    
    def add2pop(self,population,offspring):
        for ind in population:
            if ind['objective'] == offspring['objective']:
                if self.debug:
                    print("duplicated result, retrying ... ")
                return False
        population.append(offspring)
        return True
    
    def check_duplicate(self,population,code):
        for ind in population:
            if code == ind['code']:
                return True
        return False

    # def population_management(self,pop):
    #     # Delete the worst individual
    #     pop_new = heapq.nsmallest(self.pop_size, pop, key=lambda x: x['objective'])
    #     return pop_new
    
    # def parent_selection(self,pop,m):
    #     ranks = [i for i in range(len(pop))]
    #     probs = [1 / (rank + 1 + len(pop)) for rank in ranks]
    #     parents = random.choices(pop, weights=probs, k=m)
    #     return parents

    def population_init_obj(self, pop, n_p):
        fitness = Parallel(n_jobs=n_p)(delayed(self.interface_eval.evaluate)(seed['code']) for seed in pop)
        for i in range(len(pop)):
            obj = np.array(fitness[i]['avg'])
            pop[i]['objective'] = np.round(obj, 5)
            pop[i]['lower'] = np.round(np.array(fitness[i]['lower']), 5)
            pop[i]['upper'] = np.round(np.array(fitness[i]['upper']), 5)
            pop[i]['trajectory'] = fitness[i]['trajectory']
        return pop

    def population_generation(self):
        
        n_create = 2
        
        population = []

        for i in range(n_create):
            _,pop = self.get_algorithm([],'i1')
            for p in pop:
                population.append(p)
             
        return population
    
    def population_generation_seed(self,seeds,n_p):

        population = []

        fitness = Parallel(n_jobs=n_p)(delayed(self.interface_eval.evaluate)(seed['code']) for seed in seeds)

        for i in range(len(seeds)):
            try:
                seed_alg = {
                    'algorithm': seeds[i]['algorithm'],
                    'code': seeds[i]['code'],
                    'objective': None,
                    'lower': None,
                    'upper': None,
                    'trajectory': None,
                    'other_inf': None
                }

                obj = np.array(fitness[i]['avg'])
                seed_alg['objective'] = np.round(obj, 5)
                seed_alg['lower'] = np.round(np.array(fitness[i]['lower']), 5)
                seed_alg['upper'] = np.round(np.array(fitness[i]['upper']), 5)
                seed_alg['trajectory'] = fitness[i]['trajectory']
                population.append(seed_alg)

            except Exception as e:
                print("Error in seed algorithm")
                exit()

        print("Initiliazation finished! Get "+str(len(seeds))+" seed algorithms")

        return population
    

    def _get_alg(self,pop,operator):
        offspring = {
            'algorithm': None,
            'code': None,
            'opt_params': {},
            'objective': None,
            'lower': None,
            'upper': None,
            'trajectory': None,
            'other_inf': None
        }
        if operator == "i1":
            parents = None
            [offspring['code'],offspring['algorithm']] =  self.evol.i1()
        elif operator == "e1":
            parents = self.select.parent_selection(pop,self.m)
            [offspring['code'],offspring['algorithm'], offspring['opt_params']] = self.evol.e1(parents)
        elif operator == "e2":
            parents = self.select.parent_selection(pop,self.m)
            [offspring['code'],offspring['algorithm'], offspring['opt_params']] = self.evol.e2(parents)
        elif operator == "m1":
            parents = self.select.parent_selection(pop,1)
            [offspring['code'],offspring['algorithm'], offspring['opt_params']] = self.evol.m1(parents[0])
        elif operator == "m2":
            parents = self.select.parent_selection(pop,1)
            [offspring['code'],offspring['algorithm'], offspring['opt_params']] = self.evol.m2(parents[0])
        elif operator == "m3":
            parents = self.select.parent_selection(pop,1)
            [offspring['code'],offspring['algorithm']] = self.evol.m3(parents[0])
        else:
            print(f"Evolution operator [{operator}] has not been implemented ! \n")

        return parents, offspring

    def get_offspring(self, pop, operator):
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

            if self.external_optimizer=='scipy' and len(offspring['opt_params'])!=0:
                from .external_scipy import ScipyOptimizer as ExternalOptimizer
            # # This is a placeholder, nevergrad not implemented
            # elif self.external_optimizer == 'nevergrad' and len(offspring['opt_params']) != 0:
            #     from .external_nevergrad import NeverGradOptimizer as ExternalOptimizer
                try:
                    print(f"Original parameters: {offspring['opt_params']}")
                    optimizer = ExternalOptimizer(
                        interface_eval=self.interface_eval,
                        timeout=self.timeout
                    )

                    opt_result = optimizer.optimize(
                        original_code=code,
                        opt_params=offspring['opt_params'],
                        param_vars=list(offspring['opt_params'].keys()),
                        executor=concurrent.futures.ThreadPoolExecutor()
                    )

                    offspring.update({
                        'code': opt_result.optimized_code,
                        'objective': np.round(opt_result.optimized_fitness, 5),
                        'lower': np.round(opt_result.optimized_lower, 5),
                        'upper': np.round(opt_result.optimized_upper, 5),
                        'trajectory': opt_result.optimized_trajectory,
                        'opt_params': opt_result.optimized_params
                    })

                    print(f"optimized parameters: {opt_result.optimized_params}")
                except Exception as e:
                    # self.code2file(offspring['code'])
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self.interface_eval.evaluate, code)
                        fitness = future.result(timeout=self.timeout)
                        offspring['objective'] = np.round(fitness['avg'], 5)
                        offspring['lower'] = np.round(fitness['lower'], 5)
                        offspring['upper'] = np.round(fitness['upper'], 5)
                        offspring['trajectory'] = fitness['trajectory']
                        future.cancel()
            else:
                #self.code2file(offspring['code'])
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self.interface_eval.evaluate, code)
                    fitness = future.result(timeout=self.timeout)
                    offspring['objective'] = np.round(fitness['avg'], 5)
                    offspring['lower'] = np.round(fitness['lower'], 5)
                    offspring['upper'] = np.round(fitness['upper'], 5)
                    offspring['trajectory'] = fitness['trajectory']
                    future.cancel()
                    # fitness = self.interface_eval.evaluate(code)
                

        except Exception as e:
            print(e)

            offspring = {
                'algorithm': None,
                'code': None,
                'objective': None,
                'lower': None,
                'upper': None,
                'trajectory': None,
                'other_inf': None
            }
            p = None
        # Round the objective values
        return p, offspring

    def update_long_term_reevo(self, iteration):
        self.evol.long_term_reflection_reevo(iteration)

    def mimic_best_sample(self, info='', population=None, iteration=0):
        self.evol.mimic_best_sample(info, population, iteration)

    def correct_worst_sample(self, info='', population=None, iteration=0):
        self.evol.correct_worst_sample(info, population, iteration)

    def hybrid(self, info='', population=None, iteration=0):
        self.evol.hybrid(info, population, iteration)

    def multi_comparative_reflection(self, info='', population=None, iteration=0):
        self.evol.multi_comparative_reflection(info, population, iteration)

    def get_data_reflection(self, data_content, iteration):
        return self.evol.get_data_reflection_external(data_content, iteration)



    def get_algorithm(self, pop, operator):

        results = []
        try:
            results = Parallel(n_jobs=self.n_p,timeout=self.timeout+15)(delayed(self.get_offspring)(pop, operator) for _ in range(self.pop_size))
        except Exception as e:
            if self.debug:
                print(f"Error: {e}")
            print("Parallel time out .")
            
        time.sleep(2)


        out_p = []
        out_off = []

        for p, off in results:
            out_p.append(p)
            out_off.append(off)
            if self.debug:
                print(f">>> check offsprings: \n {off}")
        return out_p, out_off

