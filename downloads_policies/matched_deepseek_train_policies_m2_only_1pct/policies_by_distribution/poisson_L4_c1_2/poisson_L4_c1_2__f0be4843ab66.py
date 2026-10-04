# policy_hash: f0be4843ab66c92d662194d172d4e9c977b53125f0a524759fffe1f8a7206a7e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 28
# source_prompt_files: 1
# best_target_performance: 815.94
# best_prompt_performance: 815.94
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_230113.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 407.7983925753421  # OPT_PARAM: {"initial": 407.7983925753421, "min": 350, "max": 500, "type": "float"}
    safety_stock = 42.41657542344269  # OPT_PARAM: {"initial": 42.41657542344269, "min": 20, "max": 60, "type": "float"}
    demand_estimate = 93.84114417593625  # OPT_PARAM: {"initial": 93.84114417593625, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.7326415821587173  # OPT_PARAM: {"initial": 0.7326415821587173, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate total pipeline with weighted emphasis on near-term arrivals
    total_pipeline = sum(pipeline_orders)
    weighted_pipeline = pipeline_weight * total_pipeline + (1 - pipeline_weight) * sum(pipeline_orders[:2])

    # Inventory position = on-hand + weighted pipeline
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level based on pipeline composition
    near_term_ratio = sum(pipeline_orders[:2]) / (total_pipeline + 1e-6)
    dynamic_adjustment = 12.22300425285378  # OPT_PARAM: {"initial": 12.22300425285378, "min": 0, "max": 30, "type": "float"}

    order_up_to = base_stock + safety_stock + dynamic_adjustment

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand estimate
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
