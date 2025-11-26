import json

import numpy as np
import importlib
from .prompts import GetPrompts
import types
import warnings
import sys
import glob


class INVENTORY:
    def __init__(self, dist=None, n_train=50, n_horizon=None, order_option='order_before_sell', prompt_version='v2'):
        self.dist = dist
        self.version = prompt_version  # 'v1' = old version, 'v2' = new version
        self.prompts = GetPrompts(prompt_version=prompt_version)
        self.mode = 'train'
        self.n_horizon = n_horizon
        self.train_instances = self.load_instances(mode='train', n_traj=n_train)
        self.test_instances = self.load_instances(mode='test')
        self.instances = None
        self.option = order_option

    def load_instances(self, mode='train', n_traj=None):
        if self.dist is None:
            pattern = f"evaluation/data/*_{mode}.json"
        else:
            pattern = f"evaluation/data/{self.dist}_{mode}.json"

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
        if self.n_horizon is not None:
            for inst in final_instances:
                inst["demand"] = [0]*inst["lead_time"] + inst["demand"][:self.n_horizon]
                inst["num_periods"] = inst["lead_time"] + self.n_horizon
        return final_instances

    def evaluate_mode(self, eva, instances):
        cost_list = []
        order_matrix = []
        cost_matrix = []
        for instance in instances:
            total_cost = 0.0
            history_demand = []
            current_inventory = instance['initial_inventory']
            order_matrix_one_row = []
            cost_matrix_one_row = []

            # Initialize pipeline inventory as FIFO queue with length = lead_time
            # Each element represents orders placed in previous periods that will arrive in future
            pipeline_inventory = [0.0] * instance['lead_time']  # [oldest, ..., newest]

            for t in range(instance['num_periods']):
                # Receive incoming shipment (oldest order in pipeline)
                incoming_order = pipeline_inventory.pop(0)
                current_inventory += incoming_order

                if self.option == 'order_before_sell':
                    # Compute order amount using the inventory policy
                    if self.version == 'v1':
                        order_amount = eva.compute_order_amount(
                            current_inventory=current_inventory,
                            pipeline_inventory=pipeline_inventory.copy(),
                        )
                    else:  # v2
                        order_amount = eva.compute_order_amount(
                            on_hand_inventory=current_inventory,
                            pipeline_orders=pipeline_inventory.copy(),
                        )

                # Record current period's demand
                current_demand = instance['demand'][t]
                history_demand.append(current_demand)

                # Calculate sales and lost sales
                sales = min(current_inventory, current_demand)
                lost_sales = max(0, current_demand - sales)
                current_inventory -= sales

                if self.option == 'order_after_sell':
                    # Compute order amount using the inventory policy
                    if self.version == 'v1':
                        order_amount = eva.compute_order_amount(
                            on_hand_inventory=current_inventory,
                            pipeline_orders=pipeline_inventory.copy(),
                        )
                    else:  # v2
                        order_amount = eva.compute_order_amount(
                            on_hand_inventory=current_inventory,
                            pipeline_orders=pipeline_inventory.copy(),
                        )

                # Place new order (will arrive after lead_time periods)
                pipeline_inventory.append(order_amount)

                # Accumulate costs
                holding_cost = instance['holding_cost'] * current_inventory
                lost_sales_cost = instance['lost_sales_cost'] * lost_sales
                order_matrix_one_row.append(order_amount)
                cost_matrix_one_row.append((holding_cost, lost_sales_cost))
                total_cost += holding_cost + lost_sales_cost
            cost_list.append(total_cost)
            order_matrix.append(order_matrix_one_row)
            cost_matrix.append(cost_matrix_one_row)
        ci = self.bootstrap_ci(cost_list)
        res = {
            'avg': sum(cost_list) / len(cost_list),
            'lower': ci[0],
            'upper': ci[1],
            'trajectory': cost_list,
            'order_matrix': order_matrix,
            'cost_matrix': cost_matrix,
        }

        return res

    def evaluateGreedy(self, eva):
        res_train = self.evaluate_mode(eva, self.train_instances)
        res_test = self.evaluate_mode(eva, self.test_instances)
        res_train['test_obj'] = res_test['avg']
        return res_train

    def evaluate(self, code_string):
        # Suppress warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Create a new module object
            heuristic_module = types.ModuleType("heuristic_module")

            # Execute the code string in the new module's namespace
            exec(code_string, heuristic_module.__dict__)

            # Add the module to sys.modules so it can be imported
            sys.modules[heuristic_module.__name__] = heuristic_module

            fitness = self.evaluateGreedy(heuristic_module)

            return fitness

    @staticmethod
    def bootstrap_ci(data, n_bootstrap=1000, ci=95):
        means = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(data, size=len(data), replace=True)
            means.append(np.mean(sample))
        lower = np.percentile(means, (100 - ci) / 2)
        upper = np.percentile(means, 100 - (100 - ci) / 2)
        return lower, upper
