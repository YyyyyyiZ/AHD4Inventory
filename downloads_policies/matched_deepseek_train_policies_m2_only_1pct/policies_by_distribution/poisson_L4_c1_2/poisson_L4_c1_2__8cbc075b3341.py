# policy_hash: 8cbc075b3341e8d1f77fbdb91a68e672ca30e6480f728e0b1b06cbcbe33731d0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 804.46
# best_prompt_performance: 804.46
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_230325.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 397.5133356525552  # OPT_PARAM: {"initial": 397.5133356525552, "min": 380, "max": 460, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 50, "type": "float"}
    demand_estimate = 95.0281819538179  # OPT_PARAM: {"initial": 95.0281819538179, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.7999999999999999  # OPT_PARAM: {"initial": 0.7999999999999999, "min": 0.7, "max": 1.0, "type": "float"}
    adjustment_factor = 8.5  # OPT_PARAM: {"initial": 8.5, "min": 0, "max": 20, "type": "float"}

    # Calculate total pipeline
    total_pipeline = sum(pipeline_orders)

    # Use simple weighted pipeline (no complex near-term calculation)
    weighted_pipeline = pipeline_weight * total_pipeline

    # Inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Order-up-to level with simplified adjustment
    order_up_to = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand estimate
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
