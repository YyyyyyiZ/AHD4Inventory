import json

import numpy as np
import importlib
from .prompts import GetPrompts
import types
import warnings
import sys
import glob

class INVENTORY:
    def __init__(self, dist = None, demand=None, volatility=None):
        self.dist = dist
        self.demand = demand
        self.volatility = volatility
        self.prompts = GetPrompts()
        self.instances = self._load_instances()

    def _load_instances(self):
        # Determine the file pattern based on parameters
        if self.dist is None and self.demand is None and self.volatility is None:
            pattern = "evaluation/data/*_train_*.json"
        elif self.dist is None and self.demand is None:
            pattern = f"evaluation/data/*_train_*_{self.volatility}.json"
        elif self.dist is None and self.volatility is None:
            pattern = f"evaluation/data/*_train_{self.demand}_*.json"
        elif self.demand is None and self.volatility is None:
            pattern = f"evaluation/data/{self.dist}_train_*.json"
        elif self.dist is None:
            pattern = f"evaluation/data/*_train_{self.demand}_{self.volatility}.json"
        elif self.volatility is None:
            pattern = f"evaluation/data/{self.dist}_train_{self.demand}_*.json"
        elif self.demand is None:
            pattern = f"evaluation/data/{self.dist}_train_*_{self.volatility}.json"
        else:
            pattern = f"evaluation/data/{self.dist}_train_{self.demand}_{self.volatility}.json"
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
            total_cost = 0.0
            history_demand = []
            current_inventory = instance['initial_inventory']

            # Initialize pipeline inventory as FIFO queue with length = lead_time
            # Each element represents orders placed in previous periods that will arrive in future
            pipeline_inventory = [0.0] * instance['lead_time']  # [oldest, ..., newest]

            for t in range(instance['num_periods']):
                # Receive incoming shipment (oldest order in pipeline)
                incoming_order = pipeline_inventory.pop(0)
                current_inventory += incoming_order

                # Compute order amount using the inventory policy
                order_amount = eva.compute_order_amount(
                    current_inventory=current_inventory,
                    pipeline_inventory=pipeline_inventory.copy(),  # Pass current pipeline state
                    history_demand=history_demand.copy(),
                    holding_cost=instance['holding_cost'],
                    lost_sales_cost=instance['lost_sales_cost'],
                    lead_time=instance['lead_time']
                )

                # Place new order (will arrive after lead_time periods)
                pipeline_inventory.append(order_amount)

                # Record current period's demand
                current_demand = instance['demand'][t]
                history_demand.append(current_demand)

                # Calculate sales and lost sales
                sales = min(current_inventory, current_demand)
                lost_sales = max(0, current_demand - sales)
                current_inventory -= sales

                # Accumulate costs
                holding_cost = instance['holding_cost'] * current_inventory
                lost_sales_cost = instance['lost_sales_cost'] * lost_sales
                total_cost += holding_cost + lost_sales_cost
            cost_list.append(total_cost)
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




