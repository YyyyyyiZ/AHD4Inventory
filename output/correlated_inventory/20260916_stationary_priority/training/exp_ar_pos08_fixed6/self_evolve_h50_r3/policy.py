import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 72.61288604122132  # OPT_PARAM: {"initial": 72.61288604122132, "min": 50.0, "max": 300.0, "type": "float"}
    demand_weight = 0.18117132546428727  # OPT_PARAM: {"initial": 0.18117132546428727, "min": 0.1, "max": 1.0, "type": "float"}
    inventory_weight = 0.3134601987885489  # OPT_PARAM: {"initial": 0.3134601987885489, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.2866724805589663  # OPT_PARAM: {"initial": 0.2866724805589663, "min": 0.0, "max": 0.3, "type": "float"}
    
    demand_estimate = base_stock + demand_weight * last_demand
    inventory_adjustment = inventory_weight * on_hand_inventory
    pipeline_adjustment = pipeline_weight * sum(pipeline_orders)
    order_amount = max(0.0, demand_estimate - inventory_adjustment - pipeline_adjustment)
    return order_amount
