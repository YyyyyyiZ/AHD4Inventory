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



debug_mode = False
demands = [80]
print("Start evaluation...")
with open("results.txt", "w") as file:
    for demand_mean in demands:
        loaded_test = load_instances(f"data/test_{demand_mean}_low.json")
        time_start = time.time()
        cost = evaluation(loaded_test)
        result = (
            f"Average for instances with mean demand {demand_mean}: Cost = {cost:7.3f}, Timecost: {time.time() - time_start:7.3f}")
        print(result)
        # file.write(result + "\n")
        


