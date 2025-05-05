import json

import numpy as np
import importlib
from .prompts import GetPrompts
import types
import warnings
import sys
import glob

class INVENTORY():
    def __init__(self, demand=None, volatility=None):
        self.demand = demand
        self.volatility = volatility
        self.prompts = GetPrompts()
        self.instances = self._load_instances()

    def _load_instances(self):
        # Determine the file pattern based on parameters
        if self.demand is None and self.volatility is None:
            pattern = "evaluation/data/train_*.json"
        elif self.demand is None:
            pattern = f"evaluation/data/train_*_{self.volatility}.json"
        elif self.volatility is None:
            pattern = f"evaluation/data/train_{self.demand}_*.json"
        else:
            pattern = f"evaluation/data/train_{self.demand}_{self.volatility}.json"
        print(f"Instances loaded {pattern}......")

        # Find all matching files and load their contents
        instances = []
        for file_path in glob.glob(pattern):
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):  # If file contains a list of instances
                    instances.extend(data)
                else:  # If file contains a single instance
                    instances.append(data)
        return instances

    def evaluateGreedy(self, eva) -> float:
        cost_list = []
        for instance in self.instances:
            cost = 0
            order_arrive = [0]  # L=1
            history_inventory = []
            history_lost = []
            history_demand = []
            inventory_level = instance['initial_inventory']
            for t in range(instance['num_periods']):
                inventory_level += order_arrive[t]
                history_inventory.append(inventory_level)

                order_amount = eva.compute_order_amount(history_demand, history_inventory, history_lost,
                                                        instance['holding_cost'], instance['lost_sales_cost'])
                order_arrive.append(order_amount)

                history_demand.append(instance['demand'][t])
                sales = min(inventory_level, instance['demand'][t])
                lost_sales = max(0, instance['demand'][t] - sales)
                inventory_level -= sales

                history_lost.append(lost_sales)

                cost += instance['holding_cost'] * inventory_level + instance['lost_sales_cost'] * lost_sales
            cost_list.append(cost)
        return sum(cost_list) / len(cost_list)

        
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




