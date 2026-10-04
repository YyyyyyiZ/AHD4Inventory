# policy_hash: 544624155db5f29790f5c197dc119366fd1909dee33616542e1da5dc5761b3ff
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2122.33
# best_prompt_performance: 2124.59
# best_rel_error_pct: 0.106487
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_032354.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 900.0  # OPT_PARAM: {"initial": 900.0, "min": 400, "max": 900, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 10, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target order amount
    target_order = base_stock - inventory_position

    # Apply smoothing to reduce order volatility
    smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate expected short-term demand from pipeline
    if len(pipeline_orders) >= 3:
        short_term_coverage = sum(pipeline_orders[:3])  # Next 3 arrivals
    else:
        short_term_coverage = sum(pipeline_orders)

    # Adjust order based on short-term coverage and safety stock
    if short_term_coverage < safety_stock:
        adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 1.0, "max": 1.5, "type": "float"}
        target_order = max(target_order, safety_stock - short_term_coverage) * adjustment_factor
    else:
        adjustment_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}
        target_order = target_order * adjustment_factor

    # Apply smoothing to the final order amount
    order_amount = max(0, target_order * smoothing_factor)

    # Round to nearest integer (as required by output type)
    return order_amount
