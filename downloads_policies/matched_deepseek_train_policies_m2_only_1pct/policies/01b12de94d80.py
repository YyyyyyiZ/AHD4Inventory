# policy_hash: 01b12de94d8004ba44498b58a92ca6f3e16510809886b9e0e212137c38dc6aea
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1759.6
# best_prompt_performance: 1760.57
# best_rel_error_pct: 0.055126
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_034407.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 919.3610300412637  # OPT_PARAM: {"initial": 919.3610300412637, "min": 400, "max": 1200, "type": "float"}
    safety_stock = 130.34505968672926  # OPT_PARAM: {"initial": 130.34505968672926, "min": 50, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target order amount
    target_order = base_stock - inventory_position

    # Apply smoothing to reduce order volatility
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate expected short-term demand from pipeline
    if len(pipeline_orders) >= 3:
        short_term_coverage = sum(pipeline_orders[:3])  # Next 3 arrivals
    else:
        short_term_coverage = sum(pipeline_orders)

    # Adjust order based on short-term coverage and safety stock
    if short_term_coverage < safety_stock:
        adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.8, "max": 1.5, "type": "float"}
        target_order = max(target_order, safety_stock - short_term_coverage) * adjustment_factor
    else:
        adjustment_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
        target_order = target_order * adjustment_factor

    # Apply smoothing to the final order amount
    order_amount = max(0, target_order * smoothing_factor)

    # Round to nearest integer (as required by output type)
    return order_amount
