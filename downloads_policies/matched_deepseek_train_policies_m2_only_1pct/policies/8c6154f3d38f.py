# policy_hash: 8c6154f3d38f1c163ffd6a6a82e14ed743934efde3a692bbe9121104633c85e1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 902.32
# best_prompt_performance: 902.32
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_102127.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 237.13355775467227  # OPT_PARAM: {"initial": 237.13355775467227, "min": 180, "max": 280, "type": "float"}
    safety_stock = 35.11796904010816  # OPT_PARAM: {"initial": 35.11796904010816, "min": 15, "max": 40, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.1, "type": "float"}
    demand_forecast = 106.74500178562862  # OPT_PARAM: {"initial": 106.74500178562862, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position with full pipeline consideration
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply exponential smoothing to order amounts
    # Use a simple smoothing based on demand forecast to avoid extreme fluctuations
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure order is non-negative and reasonable
    order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
