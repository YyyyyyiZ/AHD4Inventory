# policy_hash: a680bea9c6d9a5eb78e896c4bcfbf52bcdae7036ee3985390cc842aef17c48d3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1221.78
# best_prompt_performance: 1224.64
# best_rel_error_pct: 0.234085
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_051944.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 66.02453955209225  # OPT_PARAM: {"initial": 66.02453955209225, "min": 20, "max": 120, "type": "float"}
    demand_estimate = 100.38661486701325  # OPT_PARAM: {"initial": 100.38661486701325, "min": 90, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    expected_demand_during_leadtime = demand_estimate * (len(pipeline_orders) + 1)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply proportional adjustment based on pipeline status
    pipeline_ratio = sum(pipeline_orders) / (demand_estimate * len(pipeline_orders)) if len(pipeline_orders) > 0 else 1.0
    adjustment_factor = 0.9016724256587929  # OPT_PARAM: {"initial": 0.9016724256587929, "min": 0.5, "max": 1.2, "type": "float"}

    if pipeline_ratio < 0.8:
        order_amount *= adjustment_factor * (1.0 + (0.8 - pipeline_ratio))
    elif pipeline_ratio > 1.2:
        order_amount *= adjustment_factor * (1.0 - (pipeline_ratio - 1.2) * 0.5)

    # Dynamic cap based on demand variability
    max_order_multiplier = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}
    max_order = demand_estimate * max_order_multiplier
    order_amount = min(order_amount, max_order)

    # Minimum order threshold with dynamic adjustment
    min_order_base = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 0, "max": 40, "type": "float"}
    if 0 < order_amount < min_order_base:
        order_amount = min_order_base

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
