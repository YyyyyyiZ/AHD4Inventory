# policy_hash: 3a2c494dff8d5dcdb1f6933d221771ad519cdd5707c1ff9da3099c434b8db62a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 827.62
# best_prompt_performance: 827.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_224632.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 423.7882827833122  # OPT_PARAM: {"initial": 423.7882827833122, "min": 350, "max": 500, "type": "float"}
    safety_stock = 33.78828278331525  # OPT_PARAM: {"initial": 33.78828278331525, "min": 20, "max": 60, "type": "float"}
    demand_estimate = 96.01254341827914  # OPT_PARAM: {"initial": 96.01254341827914, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate total pipeline (all orders in transit)
    total_pipeline = sum(pipeline_orders)

    # Inventory position = on-hand + all pipeline orders
    inventory_position = on_hand_inventory + total_pipeline

    # Calculate order-up-to level
    order_up_to = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing: blend with demand estimate
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
