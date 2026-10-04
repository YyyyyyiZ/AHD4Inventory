# policy_hash: bed5fc51dec24b4032a60bc0bdb2667f2a0d8972c9b2f1eaac73513447156001
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 1250.48
# best_prompt_performance: 1250.48
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_204034.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 650.0  # OPT_PARAM: {"initial": 650.0, "min": 450, "max": 650, "type": "float"}
    safety_stock = 20.598401976666782  # OPT_PARAM: {"initial": 20.598401976666782, "min": 0, "max": 40, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using average of all pipeline orders (better than just recent)
    if len(pipeline_orders) > 0:
        estimated_demand = sum(pipeline_orders) / len(pipeline_orders)
    else:
        estimated_demand = 100.0

    # Adjust base stock based on estimated demand with different multiplier
    demand_adjustment = 0.3992754244437827  # OPT_PARAM: {"initial": 0.3992754244437827, "min": 0.3, "max": 1.5, "type": "float"}
    adjusted_base = base_stock + estimated_demand * demand_adjustment

    # Calculate target inventory level
    target_inventory = adjusted_base + safety_stock

    # Order amount calculation
    order_amount = max(0, target_inventory - inventory_position)

    # Smooth ordering with reasonable limits
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 200, "type": "float"}
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 30, "type": "float"}

    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        # Limit order increase/decrease for stability
        max_increase = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 80, "type": "float"}
        order_amount = min(order_amount, last_order + max_increase)

    # Additional smoothing: don't order if inventory position is already close to target
    buffer_zone = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 5, "max": 50, "type": "float"}
    if inventory_position > target_inventory - buffer_zone and inventory_position < target_inventory + buffer_zone:
        order_amount = min(order_amount, estimated_demand)  # Order only expected demand

    order_amount = max(min_order, min(order_amount, max_order))

    return order_amount
