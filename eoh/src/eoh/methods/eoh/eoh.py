import numpy as np
import json
import random
import time
from pathlib import Path
import csv

from .eoh_interface_EC import InterfaceEC
# main class for eoh
class EOH:

    # initilization
    def __init__(self, paras, problem, select, manage, **kwargs):
        self.prob = problem
        self.select = select
        self.manage = manage
        
        # LLM settings
        self.use_local_llm = paras.llm_use_local
        self.llm_local_url = paras.llm_local_url
        self.api_endpoint = paras.llm_api_endpoint  # currently only API2D + GPT
        self.api_key = paras.llm_api_key
        self.llm_model = paras.llm_model

        # ------------------ RZ: use local LLM ------------------
        # self.use_local_llm = kwargs.get('use_local_llm', False)
        # assert isinstance(self.use_local_llm, bool)
        # if self.use_local_llm:
        #     assert 'url' in kwargs, 'The keyword "url" should be provided when use_local_llm is True.'
        #     assert isinstance(kwargs.get('url'), str)
        #     self.url = kwargs.get('url')
        # -------------------------------------------------------

        # Experimental settings       
        self.pop_size = paras.ec_pop_size  # popopulation size, i.e., the number of algorithms in population
        self.n_pop = paras.ec_n_pop  # number of populations

        self.operators = paras.ec_operators
        self.operator_weights = paras.ec_operator_weights
        if paras.ec_m > self.pop_size or paras.ec_m == 1:
            print("m should not be larger than pop size or smaller than 2, adjust it to m=2")
            paras.ec_m = 2
        self.m = paras.ec_m

        self.debug_mode = paras.exp_debug_mode  # if debug
        self.ndelay = 1  # default

        self.use_seed = paras.exp_use_seed
        self.seed_path = paras.exp_seed_path
        self.load_pop = paras.exp_use_continue
        self.load_pop_path = paras.exp_continue_path
        self.load_pop_id = paras.exp_continue_id
        self.output_path = paras.exp_output_path
        self.exp_n_proc = paras.exp_n_proc
        self.timeout = paras.eva_timeout
        self.use_numba = paras.eva_numba_decorator

        self.create_initial = paras.exp_create_initial

        self.K1 =paras.K1
        self.K2 =paras.K2
        if self.K1==0 and self.K2==0:
            self.reflect = None
        elif self.K1==0 and self.K2==1:
            self.reflect = 'correct_worst_sample'
        elif self.K1==1 and self.K2==0:
            self.reflect = 'mimic_best_sample'
        elif self.K1==1 and self.K2==1:
            self.reflect = 'hybrid'
        else:
            self.reflect = 'multi_comparative_reflection'

        self.prompt_type = paras.prompt_type

        self.background_info = paras.background_info
        if self.background_info == 'no':
            self.background_info = None

        self.external_optimizer=paras.external_optimizer
        if self.external_optimizer=='no':
            self.external_optimizer=None

        # for saving results to .csv
        self.problem = paras.problem
        self.dist = paras.dist
        self.demand_mean = paras.demand
        self.volatility = paras.volatility

        print("- EoH parameters loaded -")

        # Set a random seed
        random.seed(2025)

    # add new individual to population
    def add2pop(self, population, offspring):
        for off in offspring:
            for ind in population:
                if ind['objective'] == off['objective']:
                    if (self.debug_mode):
                        print("duplicated result, retrying ... ")
            population.append(off)

    def get_info(self, offspring_pop):
        # Start with all codes
        info = "Here are all the candidate algorithms' code implementations:\n"
        for i, offspring in enumerate(offspring_pop, 1):
            info += f"\nAlgorithm {i}:\n{offspring['code']}\n"

        # Add statistical information based on background_info
        if self.background_info == 'all':
            info += "\nHere are their corresponding performance values:\n"
            for i, offspring in enumerate(offspring_pop, 1):
                info += f"\nAlgorithm {i} performance: {offspring['objective']:.2f}\n"

        elif self.background_info == 'quantile':
            objectives = [offspring['objective'] for offspring in offspring_pop]
            q1 = np.quantile(objectives, 0.25)
            median = np.quantile(objectives, 0.5)
            q3 = np.quantile(objectives, 0.75)

            info += "\nQuantile statistics of their performance:\n"
            info += f"- 25th percentile (Q1): {q1:.2f}\n"
            info += f"- 50th percentile (Median): {median:.2f}\n"
            info += f"- 75th percentile (Q3): {q3:.2f}\n"

        else:  # avg
            avg_objective = np.mean([offspring['objective'] for offspring in offspring_pop])
            info += "\nAverage performance of all algorithms:\n"
            info += f"Mean objective value: {avg_objective:.2f}\n"

        return info


    # run eoh 
    def run(self):

        print("- Evolution Start -")

        time_start = time.time()

        # interface for large language model (llm)
        # interface_llm = PromptLLMs(self.api_endpoint,self.api_key,self.llm_model,self.debug_mode)

        # interface for evaluation
        interface_prob = self.prob

        # interface for ec operators
        interface_ec = InterfaceEC(self.pop_size, self.m, self.api_endpoint, self.api_key, self.llm_model, self.use_local_llm, self.llm_local_url,
                                   self.debug_mode, interface_prob, reflect=self.reflect, K1=self.K1, K2=self.K2,
                                   background_info = self.background_info, prompt_type=self.prompt_type,
                                   external_optimizer=self.external_optimizer,
                                   exp_output_path = self.output_path,
                                   select=self.select,n_p=self.exp_n_proc, timeout = self.timeout, use_numba=self.use_numba
                                   )

        # initialization
        population = []
        if self.use_seed:
            with open(self.seed_path) as file:
                data = json.load(file)
            population = interface_ec.population_generation_seed(data,self.exp_n_proc)
            filename = f"{self.output_path}/pops/population_generation_0.json"
            with open(filename, 'w') as f:
                json.dump(population, f, indent=5)
            n_start = 0
        else:
            if self.load_pop:  # load population from files
                print("1. Load initial population from " + self.load_pop_path)
                # import os
                # print(os.getcwd())
                with open(self.load_pop_path) as file:
                    data = json.load(file)
                for individual in data:
                    population.append(individual)
                population = interface_ec.population_init_obj(population, self.exp_n_proc)

                if self.create_initial:
                    print("2. Creating initial population...")
                    population_1 = interface_ec.population_generation()
                    population_1 = self.manage.population_management(population_1, self.pop_size)
                    for pop in population_1:
                        population.append(pop)
                else:
                    print("2. No initial population created...")

                print(f"3. Pop initial: ")
                for off in population:
                    print(" Obj: ", off['objective'], end="|")
                print()
                # Save population to a file
                filename = f"{self.output_path}/pops/population_generation_0.json"
                with open(filename, 'w') as f:
                    json.dump(population, f, indent=5)

                n_start = self.load_pop_id
            else:  # create new population
                print("creating initial population:")
                population = interface_ec.population_generation()
                population = self.manage.population_management(population, self.pop_size)

                # print(len(population))
                # if len(population)<self.pop_size:
                #     for op in [self.operators[0],self.operators[2]]:
                #         _,new_ind = interface_ec.get_algorithm(population, op)
                #         self.add2pop(population, new_ind)
                #         population = self.manage.population_management(population, self.pop_size)
                #         if len(population) >= self.pop_size:
                #             break
                #         print(len(population))
     
                
                print(f"3. Pop initial: ")
                for off in population:
                    print(" Obj: ", off['objective'], end="|")
                # Save population to a file
                filename = f"{self.output_path}/pops/population_generation_0.json"
                with open(filename, 'w') as f:
                    json.dump(population, f, indent=5)
                n_start = 0

        # main loop
        n_op = len(self.operators)

        for pop in range(n_start, self.n_pop):
            offspring_pop = []
            for i in range(n_op):
                op = self.operators[i]
                print(f" OP: {op}, [{i + 1} / {n_op}] ", end="|") 
                op_w = self.operator_weights[i]
                if (np.random.rand() < op_w):
                    parents, offsprings = interface_ec.get_algorithm(population, op)
                self.add2pop(population, offsprings)  # Check duplication, and add the new offspring
                self.add2pop(offspring_pop, offsprings)
                for off in offsprings:
                    print(" Obj: ", off['objective'], end="|")
                size_act = min(len(population), self.pop_size)
                population = self.manage.population_management(population, size_act)
                offspring_pop = self.manage.population_management(offspring_pop, size_act)
                print()
            if self.background_info:
                assert self.background_info in ['avg', 'quantile', 'all']
                info = self.get_info(offspring_pop)
            else:
                info = ''
            # if self.reflect:  # reevo style reflection
            #     interface_ec.update_long_term_reevo(iteration=pop)
            if self.reflect == 'mimic_best_sample':
                interface_ec.mimic_best_sample(info, offspring_pop, iteration=pop)
            elif self.reflect == 'correct_worst_sample':
                interface_ec.correct_worst_sample(info, offspring_pop, iteration=pop)
            elif self.reflect == 'hybrid':
                interface_ec.hybrid(info, offspring_pop, iteration=pop)
            elif self.reflect == 'multi_comparative_reflection':
                interface_ec.multi_comparative_reflection(info, offspring_pop, iteration=pop)
            else:
                pass    # No reflection


            # Save population to a file
            filename = f"{self.output_path}/pops/population_generation_" + str(pop + 1) + ".json"
            # filename = self.output_path + "/results/pops/population_generation_" + str(pop + 1) + ".json"
            with open(filename, 'w') as f:
                json.dump(population, f, indent=5)

            # Save the best one to a file
            filename = f"{self.output_path}/pops_best/population_generation_" + str(pop + 1) + ".json"
            with open(filename, 'w') as f:
                json.dump(population[0], f, indent=5)


            print(f"--- {pop + 1} of {self.n_pop} populations finished. Time Cost:  {((time.time()-time_start)/60):.1f} m")
            print("Pop Objs: ", end=" ")
            for i in range(len(population)):
                print(str(population[i]['objective']) + " ", end="")
            print()

            if pop == self.n_pop - 1:   # save results
                self.save_results(population)


    def save_results(self, population):
        parent_dir = Path(self.output_path).parent
        oneline = {
            'problem': self.problem,
            'dist': self.dist,
            'demand_mean': self.demand_mean,
            'prompt_type': self.prompt_type,
            'K1': self.K1,
            'K2': self.K2,
            'background_info': 'no' if self.background_info is None else self.background_info,
            'external_opt': 'no' if self.external_optimizer is None else self.external_optimizer,
        }

        for i in range(min(10, len(population))):
            oneline[str(i + 1)] = population[i]['objective']

        for i in range(len(population), 10):
            oneline[str(i + 1)] = None

        filename = f"{parent_dir}/res.csv"

        with open(filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[
                'problem', 'dist', 'demand_mean', 'prompt_type',
                'K1', 'K2', 'background_info', 'external_opt',
                '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'
            ])

            if csvfile.tell() == 0:
                writer.writeheader()

            writer.writerow(oneline)


