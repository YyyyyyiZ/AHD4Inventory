# -------
# Evaluaiton code for EoH on Inventory
#--------

from gen_data import load_instances
import time
import numpy as np
import importlib


def evaluation(instances):
    heuristic_module = importlib.import_module("heuristic")
    eva = importlib.reload(heuristic_module)
    cost_list = []
    for instance in instances:
        cost = 0
        order_arrive = [0]  # L=1
        history_inventory = []
        history_lost = []
        history_demand = []
        inventory_level = instance['initial_inventory']
        for t in range(instance['num_periods']):
            inventory_level += order_arrive[t]
            history_inventory.append(inventory_level)

            order_amount = eva.compute_order_amount(history_demand, history_inventory, history_lost, instance['holding_cost'], instance['lost_sales_cost'])
            order_arrive.append(order_amount)

            history_demand.append(instance['demand'][t])
            sales = min(inventory_level, instance['demand'][t])
            lost_sales = max(0, instance['demand'][t] - sales)
            inventory_level -= sales

            history_lost.append(lost_sales)

            cost += instance['holding_cost'] * inventory_level + instance['lost_sales_cost'] * lost_sales
        cost_list.append(cost)
    return sum(cost_list) / len(cost_list)



debug_mode = False
demands = [50, 60, 70, 80]
print("Start evaluation...")
with open("results.txt", "w") as file:
    for demand_mean in demands:
        loaded_test = load_instances(f"data/test_{demand_mean}_*.json")
        time_start = time.time()
        cost = evaluation(loaded_test)
        result = (
            f"Average for instances with mean demand {demand_mean}: Cost = {cost:7.3f}, Timecost: {time.time() - time_start:7.3f}")
        print(result)
        # file.write(result + "\n")
        


