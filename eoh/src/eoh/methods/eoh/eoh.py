import numpy as np
import pandas as pd
import json
import random
import time
from pathlib import Path
import csv
import glob

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
        self.repeat = paras.repeat
        self.algo_performance = paras.algo_performance
        self.data_summary = paras.data_summary

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
        if self.background_info == 'verbal':
            self.reflect = 'in_context_learning'
        if self.data_summary == 'no':
            self.data_summary = None
        self.background_type = paras.background_type
        self.data_sep = paras.data_sep
        self.cal_cost = paras.cal_cost

        self.external_optimizer=paras.external_optimizer
        if self.external_optimizer=='no':
            self.external_optimizer=None
        self.iter_opt = paras.iter_opt
        self.param_loc = paras.param_loc

        # for saving results to .csv
        self.problem = paras.problem
        self.dist = paras.dist
        self.demand_mean = paras.demand
        self.volatility = paras.volatility
        self.n_train = paras.n_train
        self.filename = paras.filename
        self.store_option = paras.store_option

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

    def get_instances(self, mode='train', n_traj=None):
        # Determine the file pattern based on parameters
        if self.dist is None and self.demand_mean is None and self.volatility is None:
            pattern = f"evaluation/data/*_{mode}_*.json"
        elif self.dist is None and self.demand_mean is None:
            pattern = f"evaluation/data/*_{mode}_*_{self.volatility}.json"
        elif self.dist is None and self.volatility is None:
            pattern = f"evaluation/data/*_{mode}_{self.demand_mean}_*.json"
        elif self.demand_mean is None and self.volatility is None:
            pattern = f"evaluation/data/{self.dist}_{mode}_*.json"
        elif self.dist is None:
            pattern = f"evaluation/data/*_{mode}_{self.demand_mean}_{self.volatility}.json"
        elif self.volatility is None:
            pattern = f"evaluation/data/{self.dist}_{mode}_{self.demand_mean}_*.json"
        elif self.demand_mean is None:
            pattern = f"evaluation/data/{self.dist}_{mode}_*_{self.volatility}.json"
        else:
            pattern = f"evaluation/data/{self.dist}_{mode}_{self.demand_mean}_{self.volatility}.json"

        # Find all matching files and load their contents
        instances = []
        for file_path in glob.glob(pattern):
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):  # If file contains a list of instances
                    instances.extend(data)
                else:  # If file contains a single instance
                    instances.append(data)
        if n_traj is not None:
            final_instances = instances[:n_traj]
        else:
            final_instances = instances
        return final_instances


    def get_data(self, offspring_pop=None, performance=False):
        instances = self.get_instances(mode='train', n_traj=self.n_train)
        data = []
        if performance:
            for idx, traj in enumerate(instances, start=1):
                trajectory_data = {
                    "trajectory_id": f"trajectory_{idx}",
                    "demand": traj["demand"],
                    f"best_codes_performance": [
                        {
                            "performance": offspring_pop[i]['trajectory'][idx - 1],
                            "global_rank": i + 1
                        }
                        for i in range(self.K1)
                    ],
                    f"worst_codes_performance": [
                        {
                            "performance": offspring_pop[-j - 1]['trajectory'][idx - 1],
                            "global_rank": len(offspring_pop) - j
                        }
                        for j in range(self.K2)
                    ]
                }
                data.append(trajectory_data)
            data = json.dumps(data, indent=2)
        else:
            for idx, traj in enumerate(instances, start=1):
                trajectory_data = {
                    "trajectory_id": f"trajectory_{idx}",
                    "demand": traj["demand"],
                }
                data.append(trajectory_data)
            data = json.dumps(data, indent=2)
        return data

    def get_data_summary(self):
        instances = self.get_instances(mode='train', n_traj=self.n_train)
        data = []
        all_demands = []

        for idx, traj in enumerate(instances, start=1):
            demand_array = np.array(traj["demand"])
            trajectory_data = {
                "trajectory_id": f"trajectory_{idx}",
                "demand": traj["demand"],
            }
            data.append(trajectory_data)
            all_demands.append(demand_array)

        # Convert list of arrays into one big array
        all_demands = np.concatenate(all_demands)

        # Basic statistics
        mean_demand = np.mean(all_demands)
        std_demand = np.std(all_demands)
        min_demand = np.min(all_demands)
        max_demand = np.max(all_demands)
        cv_demand = std_demand / mean_demand if mean_demand != 0 else float("inf")

        # Per-trajectory stats (to see diversity)
        per_traj_stats = []
        for traj in data:
            arr = np.array(traj["demand"])
            per_traj_stats.append({
                "id": traj["trajectory_id"],
                "mean": np.mean(arr),
                "std": np.std(arr),
                "min": np.min(arr),
                "max": np.max(arr)
            })

        # Construct text summary
        data_summary = []
        data_summary.append("Demand Data Summary (across all trajectories):")
        data_summary.append(f"- Total number of trajectories: {len(data)}")
        data_summary.append(f"- Total number of periods: {len(all_demands)}")
        data_summary.append(f"- Mean demand: {mean_demand:.2f}")
        data_summary.append(f"- Std deviation: {std_demand:.2f}")
        data_summary.append(f"- Min demand: {min_demand}, Max demand: {max_demand}")
        data_summary.append(f"- Coefficient of Variation (CV): {cv_demand:.2f}")

        data_summary.append("\nPer-trajectory statistics (mean ± std, min-max):")
        for stat in per_traj_stats[:5]:  # show first 5 for brevity
            data_summary.append(
                f"  • {stat['id']}: mean={stat['mean']:.2f}, std={stat['std']:.2f}, "
                f"range=({stat['min']}, {stat['max']})"
            )
        if len(per_traj_stats) > 5:
            data_summary.append(f"  ... and {len(per_traj_stats) - 5} more trajectories")

        return "\n".join(data_summary)

    def get_info(self, offspring_pop, data_reflection=None):
        # Start with all codes
        info = ""   # self.background_info == 'no', valid for both 'sep' and 'sepp'

        if self.background_info == 'avg':
            for i, offspring in enumerate(offspring_pop, 1):
                info += f"\nAlgorithm {i}:\n{offspring['code']}\n"
                info += f"Performance: {offspring['objective']}\n"

        elif self.background_info == 'interval':
            for i, offspring in enumerate(offspring_pop, 1):
                info += f"\nAlgorithm {i}:\n{offspring['code']}\n"
                info += f"Average Performance: {offspring['objective']}; 95% Confidence Interval: ({offspring['lower']}, {offspring['upper']})\n"

        elif self.background_info == 'data':
            info += (f"\nDemand dataset consists of multiple trajectories, "
                     f"each representing a time series of demand values over 50 periods.\n{self.get_data()}\n")
            for i, offspring in enumerate(offspring_pop, 1):
                info += f"\nAlgorithm {i}:\n{offspring['code']}\n"
                info += f"Performance on each trajectory: {offspring['trajectory']}\n"
                info += f"Average Performance over all trajectories: {offspring['objective']}; 95% Confidence Interval: ({offspring['lower']}, {offspring['upper']})\n"

        elif self.background_info == 'explicit':
            info += 'Demand data follows poisson distribution with mean=80.'

        elif self.background_info == 'dataonly' or self.data_sep == 'sep':
            info += (f"\nDemand dataset consists of multiple trajectories, "
                     f"each representing a time series of demand values over 50 periods.\n{self.get_data()}\n")

        elif self.background_info == 'exactdata':
            info += (f"\nThe demand dataset consists of multiple independent trajectories, each representing a complete time series of demand values across 50 consecutive periods. "
                     f"For each trajectory, we evaluate all available codes and select:\n"
                     f"- Top {self.K1} codes: Those with the highest average performance across ALL trajectories\n"
                     f"- Bottom {self.K2} codes: Those with the lowest average performance across ALL trajectories\n"
                     f"and provide these selected codes' actual performance specific to THIS particular trajectory.\n"
                     f"{self.get_data(offspring_pop, performance=True)}\n")

        elif self.background_info == 'refonly':
            info += (f"\nBased on the demand data and corresponding performance of generated codes, "
                     f"we have obtained the following key reflections:.\n{data_reflection}\n")

        elif self.background_info == 'exactdataref':
            info += (f"\nThe demand dataset consists of multiple independent trajectories. "
                     f"Each trajectory represents a complete time series of demand values across 50 consecutive periods. "
                     f"For each trajectory, we evaluate all available codes and select:\n"
                     f"- Top {self.K1} codes: Those with the highest average performance across ALL trajectories\n"
                     f"- Bottom {self.K2} codes: Those with the lowest average performance across ALL trajectories\n"
                     f"and provide these selected codes' actual performance specific to THIS particular trajectory.\n"
                     f"{self.get_data(offspring_pop, performance=True)}\n")
            info += (f"\nBased on the demand data and corresponding performance of generated codes, "
                     f"we have obtained the following key reflections:.\n{data_reflection}\n")
        elif self.background_info == 'verbal':
            n_heu = 3
            n_heu = min(n_heu, len(offspring_pop))
            n_traj = 5
            data = json.loads(self.get_data())
            sampled_traj_indices = random.sample(range(len(data)), n_traj)
            if isinstance(offspring_pop, str):
                offspring_pop = json.loads(offspring_pop)
            sampled_offspring = random.sample(offspring_pop, n_heu)
            # --- Generate heuristic descriptions (heu_descr) ---
            heu_descr = ""
            for i, offspring in enumerate(sampled_offspring, 1):
                descr = offspring['algorithm']  # Assuming the field is 'descr', not 'algorithm' as in your snippet
                heu_descr += f"- Heuristic H{i}: {descr}\n"

            # --- Generate data table (data_tab) ---
            header = "| trajectory |"   # Header: Trajectory | D_1 | D_2 | ... | Cost_H1 | Cost_H2 | ...
            demand_length = len(data[0]["demand"])  # Get the number of demand values per trajectory
            for d in range(1, demand_length + 1):   # Add D_1, D_2, ..., D_n columns
                header += f" D_{d} |"
            for h in range(1, n_heu + 1):   # Add Cost_H1, Cost_H2, ..., Cost_Hn columns
                header += f" Cost_H{h} |"
            separator = "|----------|" + "-----|" * demand_length + "--------|" * n_heu

            # Initialize the table with header and separator
            data_tab = f"{header}\n{separator}\n"

            # Populate each row with trajectory data and heuristic costs
            for kk, traj_idx in enumerate(sampled_traj_indices):
                traj_data = data[traj_idx]
                demand = traj_data["demand"]

                row = f"| {kk + 1}        |"  # Add trajectory ID and demand values
                for d in demand:
                    row += f" {d}  |"

                for offspring in sampled_offspring: # Add heuristic costs for this trajectory
                    traj_costs = offspring['trajectory'][traj_idx]  # Get cost for this trajectory
                    row += f" {traj_costs}     |"

                data_tab += f"{row}\n"

            info = [heu_descr, data_tab]

        return info


    def run(self):

        print("- Evolution Start -")

        time_start = time.time()

        # interface for large language model (llm)
        # interface_llm = PromptLLMs(self.api_endpoint,self.api_key,self.llm_model,self.debug_mode)

        # interface for evaluation
        interface_prob = self.prob

        # interface for ec operators
        interface_ec = InterfaceEC(self.pop_size, self.m, self.api_endpoint, self.api_key, self.llm_model, self.use_local_llm, self.llm_local_url,
                                   self.debug_mode, interface_prob,
                                   data_summary=self.get_data_summary() if self.data_summary else None, algo_performance=self.algo_performance,
                                   reflect=self.reflect, K1=self.K1, K2=self.K2,
                                   background_info = self.background_info, background_type=self.background_type, data_sep=self.data_sep,
                                   prompt_type=self.prompt_type,
                                   external_optimizer=self.external_optimizer, max_iter = self.iter_opt, param_loc=self.param_loc,
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
                    parents, offsprings = interface_ec.get_algorithm(population, op, n_pop=pop)
                self.add2pop(population, offsprings)  # Check duplication, and add the new offspring
                self.add2pop(offspring_pop, offsprings)
                for off in offsprings:
                    print(" Obj: ", off['objective'], end="|")
                size_act = min(len(population), self.pop_size)
                population = self.manage.population_management(population, size_act)
                offspring_pop = self.manage.population_management(offspring_pop, size_act)
                print()
            if pop != self.n_pop-1:
                if self.background_info:
                    # assert self.background_info in ['avg', 'quantile', 'all']
                    data_reflection = None
                    if self.data_sep in ['sepp'] and self.background_info in ['refonly', 'exactdataref']:
                        try:
                            data_reflection = interface_ec.get_data_reflection(
                                self.get_data(offspring_pop, performance=True), iteration=pop)
                        except:
                            data_reflection = interface_ec.get_data_reflection(
                                self.get_data(population, performance=True), iteration=pop)
                    try:
                        if self.background_info == 'verbal':
                            info = self.get_info(population, data_reflection)
                        else:
                            info = self.get_info(offspring_pop, data_reflection)
                    except:
                        info = self.get_info(population, data_reflection)
                else:
                    info = ''
                # if self.reflect:  # reevo style reflection
                #     interface_ec.update_long_term_reevo(iteration=pop)
                if self.reflect == 'mimic_best_sample':
                    try:
                        interface_ec.mimic_best_sample(info, offspring_pop, iteration=pop)
                    except:
                        interface_ec.mimic_best_sample(population, population, iteration=pop)
                elif self.reflect == 'correct_worst_sample':
                    try:
                        interface_ec.correct_worst_sample(info, offspring_pop, iteration=pop)
                    except:
                        interface_ec.correct_worst_sample(info, population, iteration=pop)
                elif self.reflect == 'hybrid':
                    try:
                        interface_ec.hybrid(info, offspring_pop, iteration=pop)
                    except:
                        interface_ec.hybrid(info, population, iteration=pop)
                elif self.reflect == 'multi_comparative_reflection':
                    try:
                        interface_ec.multi_comparative_reflection(info, offspring_pop, iteration=pop)
                    except:
                        interface_ec.multi_comparative_reflection(info, population, iteration=pop)
                elif self.reflect == 'in_context_learning':
                    interface_ec.in_context_learning(info, iteration=pop)
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

            self.save_results(population, pop + 1, 'train')
            self.save_results(population, pop + 1, 'test')


    def save_results(self, population, pop_idx, mode='train'):
        parent_dir = Path(self.output_path).parent
        oneline = {
            'problem': self.problem,
            'dist': self.dist,
            'demand_mean': self.demand_mean,
            'n_train': self.n_train,
            'prompt_type': self.prompt_type,
            'K1': self.K1,
            'K2': self.K2,
            'background_info': 'no' if self.background_info is None else self.background_info,
            'background_type': self.background_type,
            'data_sep': self.data_sep,
            'cal_cost': self.cal_cost,
            'external_opt': 'no' if self.external_optimizer is None else self.external_optimizer,
            'iter_opt': '-' if self.external_optimizer is None else self.iter_opt,
            'param_loc': '-' if self.external_optimizer is None else self.param_loc,
            'repeat': self.repeat,
            'n_pop': pop_idx,
            'mode': mode,
        }
        if mode == 'train':
            for i in range(min(30, len(population))):
                oneline[str(i + 1)] = population[i]['objective']
        elif mode == 'test':
            for i in range(min(30, len(population))):
                oneline[str(i + 1)] = population[i]['test_objective']

        for i in range(len(population), 30):
            oneline[str(i + 1)] = None


        filename = f"{parent_dir}/{self.filename}.csv"
        fieldnames = [
            'problem', 'dist', 'demand_mean', 'n_train', 'prompt_type',
            'K1', 'K2', 'background_info', 'background_type', 'data_sep',
            'cal_cost', 'external_opt', 'iter_opt', 'param_loc', 'repeat',
            'pop_idx', 'mode',
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
            '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
            '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
        ]

        try:
            df = pd.read_csv(filename)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df = pd.DataFrame(columns=fieldnames)

        new_row = pd.DataFrame([oneline])

        if self.store_option == 'cover':
            mask = (
                    (df['problem'] == oneline['problem']) &
                    (df['dist'] == oneline['dist']) &
                    (df['demand_mean'] == oneline['demand_mean']) &
                    (df['n_train'] == oneline['n_train']) &
                    (df['prompt_type'] == oneline['prompt_type']) &
                    (df['K1'] == oneline['K1']) &
                    (df['K2'] == oneline['K2']) &
                    (df['repeat'] == oneline['repeat']) &
                    (df['pop_idx'] == oneline['pop_idx']) &
                    (df['mode'] == oneline['mode']) &
                    (df['background_info'] == oneline['background_info']) &
                    (df['background_type'] == oneline['background_type']) &
                    (df['data_sep'] == oneline['data_sep']) &
                    (df['cal_cost'] == oneline['cal_cost']) &
                    (df['iter_opt'] == oneline['iter_opt']) &
                    (df['param_loc'] == oneline['param_loc']) &
                    (df['external_opt'] == oneline['external_opt'])
            )

            if mask.any():
                df.loc[mask] = new_row.values
            else:
                df = pd.concat([df, new_row], ignore_index=True)
        elif self.store_option == 'append':
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            raise ValueError(f"Unknown store_option: {self.store_option}")

        df.to_csv(filename, index=False, float_format='%.4f')


