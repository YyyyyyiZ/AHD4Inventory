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
        self.background_type = paras.background_type
        self.data_sep = paras.data_sep
        self.cal_cost = paras.cal_cost

        self.external_optimizer=paras.external_optimizer
        if self.external_optimizer=='no':
            self.external_optimizer=None

        # for saving results to .csv
        self.problem = paras.problem
        self.dist = paras.dist
        self.demand_mean = paras.demand
        self.volatility = paras.volatility
        self.filename = paras.filename

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

    # def get_info(self, offspring_pop):
    #     # Start with all codes
    #     info = "Here are all the candidate algorithms' code implementations:\n"
    #     for i, offspring in enumerate(offspring_pop, 1):
    #         info += f"\nAlgorithm {i}:\n{offspring['code']}\n"
    #
    #     # Add statistical information based on background_info
    #     if self.background_info == 'all':
    #         info += "\nHere are their corresponding performance values:\n"
    #         for i, offspring in enumerate(offspring_pop, 1):
    #             info += f"\nAlgorithm {i} performance: {offspring['objective']:.2f}\n"
    #
    #     elif self.background_info == 'quantile':
    #         objectives = [offspring['objective'] for offspring in offspring_pop]
    #         q1 = np.quantile(objectives, 0.25)
    #         median = np.quantile(objectives, 0.5)
    #         q3 = np.quantile(objectives, 0.75)
    #
    #         info += "\nQuantile statistics of their performance:\n"
    #         info += f"- 25th percentile (Q1): {q1:.2f}\n"
    #         info += f"- 50th percentile (Median): {median:.2f}\n"
    #         info += f"- 75th percentile (Q3): {q3:.2f}\n"
    #
    #     else:  # avg
    #         avg_objective = np.mean([offspring['objective'] for offspring in offspring_pop])
    #         info += "\nAverage performance of all algorithms:\n"
    #         info += f"Mean objective value: {avg_objective:.2f}\n"
    #
    #     return info

    def get_instances(self):
        # Determine the file pattern based on parameters
        if self.dist is None and self.demand_mean is None and self.volatility is None:
            pattern = "evaluation/data/*_train_*.json"
        elif self.dist is None and self.demand_mean is None:
            pattern = f"evaluation/data/*_train_*_{self.volatility}.json"
        elif self.dist is None and self.volatility is None:
            pattern = f"evaluation/data/*_train_{self.demand_mean}_*.json"
        elif self.demand_mean is None and self.volatility is None:
            pattern = f"evaluation/data/{self.dist}_train_*.json"
        elif self.dist is None:
            pattern = f"evaluation/data/*_train_{self.demand_mean}_{self.volatility}.json"
        elif self.volatility is None:
            pattern = f"evaluation/data/{self.dist}_train_{self.demand_mean}_*.json"
        elif self.demand_mean is None:
            pattern = f"evaluation/data/{self.dist}_train_*_{self.volatility}.json"
        else:
            pattern = f"evaluation/data/{self.dist}_train_{self.demand_mean}_{self.volatility}.json"

        # Find all matching files and load their contents
        instances = []
        for file_path in glob.glob(pattern):
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    instances.extend(data)
                else:
                    instances.append(data)
        return instances

    def get_param(self):
        instance = self.get_instances()[0]
        param_desc = (
            f"Specifically, current inventory system in consideration has initial stock I_0={instance['initial_inventory']} units, "
            f"operates over T={instance['num_periods']} periods with lead time L={instance['lead_time']}, "
            f"where holding cost h={instance['holding_cost']} per unit and "
            f"lost sales penalty p={instance['lost_sales_cost']} per unit."
        )
        return param_desc



    def get_data(self, offspring_pop=None, performance=False):
        instances = self.get_instances()
        if performance:
            data = []
            for idx, traj in enumerate(instances, start=1):
                trajectory_data = {
                    "trajectory_id": f"trajectory_{idx}",
                    "demand": traj["demand"],
                    f"best_codes_performance": [
                        {
                            "performance": offspring_pop[i]['trajectory'][idx-1],
                            "global_rank": i + 1
                        }
                        for i in range(self.K1)
                    ],
                    f"worst_codes_performance": [
                        {
                            "performance": offspring_pop[-j - 1]['trajectory'][idx-1],
                            "global_rank": len(offspring_pop) - j
                        }
                        for j in range(self.K2)
                    ]
                }
                data.append(trajectory_data)
            data = json.dumps(data, indent=2)
        else:
            data = []
            for idx, traj in enumerate(instances, start=1):
                trajectory_data = {
                    "trajectory_id": f"trajectory_{idx}",
                    "demand": traj["demand"],
                }
                data.append(trajectory_data)
            data = json.dumps(data, indent=2)
        return data


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

        if self.cal_cost == 'code':
            info += """
Below is the code for calculating total costs:

```python
def cost_calculation(
    I_0: float,          # Initial inventory
    d: list[float],      # Demand per period [d_1, ..., d_T] 
    L: int,              # Lead time
    h: float,            # Holding cost rate
    p: float,            # Lost sales penalty
    policy_fn: callable  # Order policy q_t = f(I_t, B_t, d_hist)
) -> float:
    
    # Computes total inventory cost over T periods: Total Cost = ∑_{t=1}^T (h·I_t + p·LS_t)
    I_t, cost = I_0, 0.0
    B_t = [0.0]*L       # Pipeline orders [q_{t-L}, ..., q_{t-1}]
    d_hist = []         # Demand history
    
    for d_t in d:
        I_t += B_t.pop(0)  # 1. Receive incoming order
        q_t = policy_fn(I_t, B_t.copy(), d_hist.copy(), h, p, L)    # 2. Place new order (arrives after L periods)
        B_t.append(q_t)
        S_t = min(I_t, d_t) # 3. Fulfill demand
        LS_t = max(0, d_t - S_t)
        I_t -= S_t
        cost += h*I_t + p*LS_t  # 4. Accumulate costs
        d_hist.append(d_t)
    return cost
                    """
            info += self.get_param()

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
                                   background_info = self.background_info, background_type=self.background_type, data_sep=self.data_sep,
                                   prompt_type=self.prompt_type,
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
            if pop != self.n_pop-1:
                if self.background_info:
                    # assert self.background_info in ['avg', 'quantile', 'all']
                    data_reflection = None
                    if self.data_sep in ['sepp'] and self.background_info in ['refonly', 'exactdataref']:
                        data_reflection = interface_ec.get_data_reflection(self.get_data(offspring_pop, performance=True), iteration=pop)
                    info = self.get_info(offspring_pop, data_reflection)
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
            'background_type': self.background_type,
            'data_sep': self.data_sep,
            'cal_cost': self.cal_cost,
            'external_opt': 'no' if self.external_optimizer is None else self.external_optimizer,
            'repeat': self.repeat,
        }

        for i in range(min(30, len(population))):
            oneline[str(i + 1)] = population[i]['objective']

        for i in range(len(population), 30):
            oneline[str(i + 1)] = None


        filename = f"{parent_dir}/{self.filename}.csv"

        # with open(filename, 'a', newline='') as csvfile:
        #     writer = csv.DictWriter(csvfile, fieldnames=[
        #         'problem', 'dist', 'demand_mean', 'prompt_type',
        #         'K1', 'K2', 'background_info', 'external_opt',
        #         '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'
        #     ])
        #
        #     if csvfile.tell() == 0:
        #         writer.writeheader()
        #
        #     writer.writerow(oneline)

        # 定义所有字段名
        fieldnames = [
            'problem', 'dist', 'demand_mean', 'prompt_type',
            'K1', 'K2', 'background_info', 'external_opt', 'repeat',
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
            '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
            '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
        ]

        # 尝试读取现有文件
        try:
            df = pd.read_csv(filename)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df = pd.DataFrame(columns=fieldnames)

        # 将新数据转换为DataFrame
        new_row = pd.DataFrame([oneline])

        # 计算统计量
        # values = new_row[[str(i) for i in range(1, 11)]].values[0]
        # values = [float(x) for x in values if str(x).replace('.', '').isdigit()]

        # if values:  # 确保有有效值
        #     new_row['avg'] = np.mean(values)
        #     new_row['25%'] = np.percentile(values, 25)
        #     new_row['50%'] = np.percentile(values, 50)
        #     new_row['75%'] = np.percentile(values, 75)

        mask = (
                (df['problem'] == oneline['problem']) &
                (df['dist'] == oneline['dist']) &
                (df['demand_mean'] == oneline['demand_mean']) &
                (df['prompt_type'] == oneline['prompt_type']) &
                (df['K1'] == oneline['K1']) &
                (df['K2'] == oneline['K2']) &
                (df['repeat'] == oneline['repeat']) &
                (df['background_info'] == oneline['background_info']) &
                (df['external_opt'] == oneline['external_opt'])
        )

        if mask.any():
            # 更新现有行
            df.loc[mask] = new_row.values
        else:
            # 添加新行
            df = pd.concat([df, new_row], ignore_index=True)

        # 保存回CSV
        df.to_csv(filename, index=False, float_format='%.4f')


