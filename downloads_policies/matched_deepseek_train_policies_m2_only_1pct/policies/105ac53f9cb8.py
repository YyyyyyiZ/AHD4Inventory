# policy_hash: 105ac53f9cb8ee81f364731d6584dd08a9c80dc5591ec11c4fe02a58d860c379
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1106.84
# best_prompt_performance: 1106.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075513.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 434.00000000014313  # OPT_PARAM: {"initial": 434.00000000014313, "min": 350, "max": 500, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 10, "max": 40, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic order-up-to level based on pipeline status
    order_up_to = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with last order reference
    last_order = pipeline_orders[-1] if pipeline_orders else raw_order
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
