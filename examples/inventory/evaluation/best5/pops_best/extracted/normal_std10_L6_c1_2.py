# Auto-extracted policy code
# Source JSON: normal_std10_L6_c1_2.json
# Extracted at: 2026-01-03 22:47:14

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 664.9760660333361  # OPT_PARAM: {"initial": 664.9760660333361, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 69.19061063558321  # OPT_PARAM: {"initial": 69.19061063558321, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 124.28848017443156  # OPT_PARAM: {"initial": 124.28848017443156, "min": 50, "max": 150, "type": "float"}
    
    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    
    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock
    
    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)
    
    # Cap order amount to avoid excessive ordering
    max_order = 95.74782422980927  # OPT_PARAM: {"initial": 95.74782422980927, "min": 50, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)
    
    return order_amount
