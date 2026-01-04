# Auto-extracted policy code
# Source JSON: poisson_L6_c1_2.json
# Extracted at: 2026-01-03 22:47:14

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9895492381544  # OPT_PARAM: {"initial": 663.9895492381544, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 58.76116633627653  # OPT_PARAM: {"initial": 58.76116633627653, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 126.02654356755875  # OPT_PARAM: {"initial": 126.02654356755875, "min": 50, "max": 150, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    
    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock
    
    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)
    
    # Cap order amount to avoid excessive ordering
    max_order = 95.92075836356183  # OPT_PARAM: {"initial": 95.92075836356183, "min": 50, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)
    
    # Round to nearest integer since order amount must be integer
    order_amount = int(round(order_amount))
    
    return order_amount
