import numpy as np
import pandas as pd
import json
import random
import time
from pathlib import Path

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

        # Experimental settings       
        self.pop_size = paras.ec_pop_size  # population size, i.e., the number of algorithms in population
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

        self.external_optimizer = paras.external_optimizer
        if self.external_optimizer == 'no':
            self.external_optimizer = None
        self.iter_opt = paras.iter_opt
        self.param_loc = paras.param_loc

        # for saving results to .csv
        self.problem = paras.problem
        self.n_train = paras.n_train
        self.n_horizon = paras.n_horizon
        self.filename = paras.filename
        self.store_option = paras.store_option

        # inventory
        self.dist = paras.dist
        self.demand_mean = paras.demand
        self.volatility = paras.volatility
        # tsp
        self.option = paras.option
        self.n_node = paras.n_node

        if self.problem == 'inventory2':
            from ...problems.optimization.inventory2.analyze import InventoryAnalyzer as Analyzer
            self.analyzer = Analyzer(self.prob, self.n_train, self.data_summary, self.algo_performance,
                                     param_info='yes')

        if self.problem == 'inventory_ex':
            from ...problems.optimization.inventory_ex.analyze import InventoryAnalyzer as Analyzer
            self.analyzer = Analyzer(self.prob, self.n_train, self.data_summary, self.algo_performance,
                                     param_info='yes')

        elif self.problem == 'tsp' and self.option == 'deterministic':
            from ...problems.optimization.tsp.analyze_deterministic import TSPAnalyzer as Analyzer
            self.analyzer = Analyzer(self.prob, self.n_train, self.data_summary, self.algo_performance,
                                     param_info='yes')

        elif self.problem == 'tsp' and self.option == 'stochastic':
            from ...problems.optimization.tsp.analyze_stochastic import TSPAnalyzer as Analyzer
            self.analyzer = Analyzer(self.prob, self.n_train, self.data_summary, self.algo_performance,
                                     param_info='yes')

        else:
            from ...problems.optimization.tsp.analyze_stochastic import TSPAnalyzer as Analyzer
            self.analyzer = Analyzer(self.prob, self.n_train, None, 'no',
                                     param_info=None)

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

    def run(self):

        print("- Evolution Start -")

        time_start = time.time()

        # interface for large language model (llm)
        # interface_llm = PromptLLMs(self.api_endpoint,self.api_key,self.llm_model,self.debug_mode)

        # interface for evaluation
        interface_prob = self.prob

        # interface for ec operators
        interface_ec = InterfaceEC(self.pop_size, self.m, self.api_endpoint, self.api_key, self.llm_model,
                                   self.use_local_llm, self.llm_local_url,
                                   self.debug_mode, interface_prob, self.analyzer,
                                   external_optimizer=self.external_optimizer, max_iter=self.iter_opt,
                                   param_loc=self.param_loc, exp_output_path=self.output_path,
                                   select=self.select, n_p=self.exp_n_proc, timeout=self.timeout,
                                   use_numba=self.use_numba
                                   )

        # initialization
        population = []
        if self.use_seed:
            with open(self.seed_path) as file:
                data = json.load(file)
            population = interface_ec.population_generation_seed(data, self.exp_n_proc)
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

            # Save population to a file
            filename = f"{self.output_path}/pops/population_generation_" + str(pop + 1) + ".json"
            # filename = self.output_path + "/results/pops/population_generation_" + str(pop + 1) + ".json"
            with open(filename, 'w') as f:
                json.dump(population, f, indent=5)

            # Save the best one to a file
            filename = f"{self.output_path}/pops_best/population_generation_" + str(pop + 1) + ".json"
            with open(filename, 'w') as f:
                json.dump(population[0], f, indent=5)

            print(
                f"--- {pop + 1} of {self.n_pop} populations finished. Time Cost:  {((time.time() - time_start) / 60):.1f} m")
            print("Pop Objs: ", end=" ")
            for i in range(len(population)):
                print(str(population[i]['objective']) + " ", end="")
            print()

            self.save_results(population, pop + 1, 'train')
            self.save_results(population, pop + 1, 'test')

    def save_results(self, population, pop_idx, mode='train'):
        from pathlib import Path
        import pandas as pd

        parent_dir = Path(self.output_path).parent
        filename = parent_dir / f"{self.filename}.csv"

        # 基本字段（注意：不再包含 'repeat'）
        oneline = {
            'LLM': self.llm_model,
            'problem': self.problem,
            'n_train': self.n_train,
            'n_horizon': self.n_horizon,
            'external_opt': 'no' if self.external_optimizer is None else self.external_optimizer,
            'iter_opt': '-' if self.external_optimizer is None else self.iter_opt,
            'param_loc': '-' if self.external_optimizer is None else self.param_loc,
            'n_pop': pop_idx,
            'mode': mode,
            'data_summary': self.data_summary,
            'algo_performance': self.algo_performance
        }

        # problem-specific 字段
        problem_fields = {
            'inventory2': {
                'dist': getattr(self, 'dist', None),
                'demand_mean': getattr(self, 'demand_mean', None)
            },
            'tsp': {
                'option': getattr(self, 'option', None),
                'n_node': getattr(self, 'n_node', None)
            },
            # more problems ...
        }
        if self.problem in problem_fields:
            oneline.update(problem_fields[self.problem])

        # score: population 假设只有一个元素
        if len(population) == 0:
            score_value = None
        else:
            if mode == 'train':
                score_value = population[0].get('objective')
            else:
                score_value = population[0].get('test_objective')

        # 读取已有文件或创建空的 dataframe（包含基础和 problem-specific 列）
        try:
            df = pd.read_csv(filename)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            problem_specific_fields = sorted({k for d in problem_fields.values() for k in d.keys()})
            base_fields = [
                'LLM', 'problem', 'n_train', 'n_horizon', 'external_opt', 'iter_opt',
                'param_loc', 'n_pop', 'mode', 'data_summary', 'algo_performance'
            ]
            df = pd.DataFrame(columns=base_fields + problem_specific_fields)

        # # 如果存在旧的 'repeat' 列，移除（你要求去掉这个字段）
        # if 'repeat' in df.columns:
        #     df = df.drop(columns=['repeat'])

        # 确保所有 oneline 的键都在 df 中（若缺失则添加列）
        key_fields = list(oneline.keys())
        for k in key_fields:
            if k not in df.columns:
                df[k] = None

        # 用你说的行判断方式：比较关键字段是否完全相等
        # 这里保留你原来的判定方法
        if df.empty:
            mask = pd.Series(dtype=bool)
        else:
            # 把 oneline 转为 Series（index 对齐 key_fields），然后比较
            cmp_series = pd.Series(oneline)
            mask = (df[key_fields] == cmp_series[key_fields]).all(axis=1)

        # 要写入的列名直接由 self.repeat 决定
        repeat_col = f"repeat_{self.repeat}"

        if mask.any():
            # 已有匹配行 -> 在该行的 repeat_col 写入 score_value
            row_idx = mask[mask].index[0]
            if repeat_col not in df.columns:
                df[repeat_col] = None
            df.at[row_idx, repeat_col] = score_value
        else:
            # 新行：把 oneline 的字段放进去，并在 repeat_col 放入 score_value
            # 先确保 df 包含 repeat_col（以便后续 concat 时列对齐）
            if repeat_col not in df.columns:
                df[repeat_col] = None

            # 准备一行完整的 new_row（包含 df 所有列）
            new_row = {col: None for col in df.columns}
            for k, v in oneline.items():
                if k in new_row:
                    new_row[k] = v
                else:
                    # 若 df 之前没有该列，则直接添加该列到 new_row（并随后确保 df 也有该列）
                    new_row[k] = v
            new_row[repeat_col] = score_value

            # 如果 oneline 含有 df 中没有的列，先扩展 df 的列（保持列对齐）
            for k in new_row.keys():
                if k not in df.columns:
                    df[k] = None

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # 保存回 CSV
        df.to_csv(filename, index=False, float_format='%.2f')

    # def save_results(self, population, pop_idx, mode='train'):
    #     parent_dir = Path(self.output_path).parent
    #
    #     oneline = {
    #         'LLM': self.llm_model,
    #         'problem': self.problem,
    #         'n_train': self.n_train,
    #         'n_horizon': self.n_horizon,
    #         'external_opt': 'no' if self.external_optimizer is None else self.external_optimizer,
    #         'iter_opt': '-' if self.external_optimizer is None else self.iter_opt,
    #         'param_loc': '-' if self.external_optimizer is None else self.param_loc,
    #         'repeat': self.repeat,
    #         'n_pop': pop_idx,
    #         'mode': mode,
    #         'data_summary': self.data_summary,
    #         'algo_performance': self.algo_performance
    #     }
    #
    #     problem_fields = {
    #         'inventory2': {
    #             'dist': getattr(self, 'dist', None),
    #             'demand_mean': getattr(self, 'demand_mean', None)
    #         },
    #         'tsp': {
    #             'option': getattr(self, 'option', None),
    #             'n_node': getattr(self, 'n_node', None)
    #         },
    #         # More problems
    #         # 'new_problem': {...}
    #     }
    #
    #     if self.problem in problem_fields:
    #         oneline.update(problem_fields[self.problem])
    #
    #     if mode == 'train':
    #         for i in range(min(30, len(population))):
    #             oneline[str(i + 1)] = population[i]['objective']
    #     elif mode == 'test':
    #         for i in range(min(30, len(population))):
    #             oneline[str(i + 1)] = population[i]['test_objective']
    #
    #     for i in range(len(population), 30):
    #         oneline[str(i + 1)] = None
    #
    #     base_fields = [
    #         'LLM', 'problem', 'n_train', 'external_opt', 'iter_opt',
    #         'param_loc', 'repeat', 'n_pop', 'mode',
    #         'data_summary', 'algo_performance'
    #     ]
    #     problem_specific_fields = set().union(*problem_fields.values())
    #     score_fields = [str(i) for i in range(1, 31)]
    #     fieldnames = base_fields + list(problem_specific_fields) + score_fields
    #
    #     filename = f"{parent_dir}/{self.filename}.csv"
    #
    #     try:
    #         df = pd.read_csv(filename)
    #     except (FileNotFoundError, pd.errors.EmptyDataError):
    #         df = pd.DataFrame(columns=fieldnames)
    #
    #     new_row = pd.DataFrame([oneline])
    #
    #     df = pd.concat([df, new_row], ignore_index=True)
    #     df.to_csv(filename, index=False, float_format='%.2f')
