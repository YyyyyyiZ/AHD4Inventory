# policy_hash: 78ae1fe97e3f3a9fbb9241ddbb2faaceea4d050791154de1405d0a5f61cc7cb8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 5889.7
# best_prompt_performance: 5889.7
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_070444.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 300.64016594478596  # OPT_PARAM: {"initial": 300.64016594478596, "min": 200, "max": 500, "type": "float"}
    safety_stock = 57.60234330684528  # OPT_PARAM: {"initial": 57.60234330684528, "min": 40, "max": 180, "type": "float"}
    pipeline_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 1.0, "type": "float"}
    demand_estimate = 127.93646205874973  # OPT_PARAM: {"initial": 127.93646205874973, "min": 70, "max": 300, "type": "float"}
    lost_sales_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust safety stock based on cost ratio (p/h = 2)
    adjusted_safety = safety_stock * lost_sales_weight

    # Calculate pipeline coverage with stronger discount
    pipeline_coverage = sum(pipeline_orders) * pipeline_factor

    # Target inventory: base + adjusted safety - discounted pipeline
    target_inventory = base_stock + adjusted_safety - pipeline_coverage

    # Ensure minimum target is proportional to expected demand
    min_target = demand_estimate * 1.5
    target_inventory = max(target_inventory, min_target)

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    if order_needed > 0:
        # Cap order based on expected demand and current pipeline
        max_order = demand_estimate * 2.5 + max(0, -order_needed * 0.3)
        capped_order = min(order_needed, max_order)

        # Apply stronger smoothing for stability
        smoothed_order = capped_order * smoothing
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
