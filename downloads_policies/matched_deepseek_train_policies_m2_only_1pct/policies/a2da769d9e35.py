# policy_hash: a2da769d9e354117b5390f239505305cd4e74ef5b74b666a0f479d11a6b0ecfd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 744.65
# best_prompt_performance: 744.62
# best_rel_error_pct: 0.004029
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_103609.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 379.9615366145842  # OPT_PARAM: {"initial": 379.9615366145842, "min": 300, "max": 450, "type": "float"}
    safety_stock = 24.961536614584112  # OPT_PARAM: {"initial": 24.961536614584112, "min": 10, "max": 50, "type": "float"}
    demand_adjustment = 0.9198538386979948  # OPT_PARAM: {"initial": 0.9198538386979948, "min": 0.8, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand based on lead time
    lead_time = len(pipeline_orders)
    estimated_demand = 99.9615366145841  # OPT_PARAM: {"initial": 99.9615366145841, "min": 80, "max": 120, "type": "float"}

    # Calculate target inventory with adjusted demand forecast
    target_inventory = base_stock + safety_stock + (estimated_demand * demand_adjustment)

    # Calculate order amount
    order_amount = max(0, target_inventory - net_inventory)

    # Apply ordering constraints
    min_order = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0, "max": 10, "type": "float"}
    max_order = 96.27877863047617  # OPT_PARAM: {"initial": 96.27877863047617, "min": 80, "max": 150, "type": "float"}

    # Smooth ordering with rounding to nearest integer
    order_amount = round(order_amount)

    if order_amount < min_order:
        order_amount = 0
    elif order_amount > max_order:
        order_amount = max_order

    return order_amount
