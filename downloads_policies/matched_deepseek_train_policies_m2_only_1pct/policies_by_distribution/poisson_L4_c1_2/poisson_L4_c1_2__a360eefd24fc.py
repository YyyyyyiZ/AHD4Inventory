# policy_hash: a360eefd24fc975629a901fb0c954bdf290b9097c606d5c8995e9ede23543ff2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1526.36
# best_prompt_performance: 1526.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074825.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 477.06320171930696  # OPT_PARAM: {"initial": 477.06320171930696, "min": 300, "max": 600, "type": "float"}
    safety_stock = 94.48282463415389  # OPT_PARAM: {"initial": 94.48282463415389, "min": 20, "max": 150, "type": "float"}
    pipeline_coef = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_adj_factor = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 0.7, "max": 1.1, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline status
    weighted_pipeline = sum(p * pipeline_weight**i for i, p in enumerate(pipeline_orders))
    adjusted_base = base_stock * (1 + 0.1 * (weighted_pipeline / (base_stock * len(pipeline_orders)) - 1))

    # Apply demand adjustment factor
    target_level = adjusted_base * demand_adj_factor + safety_stock

    # Calculate order amount
    order_amount = max(0, target_level - inventory_position)

    # Apply pipeline coefficient for smoothing
    order_amount = pipeline_coef * order_amount

    # Round to nearest integer
    return order_amount
