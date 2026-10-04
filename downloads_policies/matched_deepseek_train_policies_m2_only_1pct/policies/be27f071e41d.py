# policy_hash: be27f071e41d3667a9c382a3813f280af43568fad10fd652450bff7f5adcc731
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1099.88
# best_prompt_performance: 1099.84
# best_rel_error_pct: 0.003637
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074437.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 415.00000000024477  # OPT_PARAM: {"initial": 415.00000000024477, "min": 350, "max": 450, "type": "float"}
    safety_stock = 30.000000000245848  # OPT_PARAM: {"initial": 30.000000000245848, "min": 15, "max": 35, "type": "float"}
    demand_forecast = 105.0  # OPT_PARAM: {"initial": 105.0, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.75, "max": 0.95, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.25, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Simple order-up-to policy
    order_up_to = base_stock * (demand_forecast / 100.0) + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing using last order as reference
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
