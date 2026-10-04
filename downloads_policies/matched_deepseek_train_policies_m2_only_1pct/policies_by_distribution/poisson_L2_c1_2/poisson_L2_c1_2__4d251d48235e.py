# policy_hash: 4d251d48235e7a6f0b9910ae583e344dffba8ef08b8c5c0687ca434455b3df88
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 712.49
# best_prompt_performance: 712.49
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_024401.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 257.22652213052487  # OPT_PARAM: {"initial": 257.22652213052487, "min": 250, "max": 320, "type": "float"}
    safety_stock = 40.01383135065465  # OPT_PARAM: {"initial": 40.01383135065465, "min": 40, "max": 80, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic adjustment based on pipeline status
    pipeline_ratio = sum(pipeline_orders) / (demand_forecast * len(pipeline_orders)) if len(pipeline_orders) > 0 else 1.0
    adjustment_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.25, "type": "float"}

    # Adjust base stock based on pipeline status
    if pipeline_ratio < 0.8:
        adjusted_base = base_stock * (1 + adjustment_factor)
    elif pipeline_ratio > 1.2:
        adjusted_base = base_stock * (1 - adjustment_factor)
    else:
        adjusted_base = base_stock

    order_up_to = adjusted_base + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing only for very large orders
    smoothing_threshold = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.3, "type": "float"}

    if order_amount > smoothing_threshold:
        excess = order_amount - smoothing_threshold
        smoothed_excess = smoothing_factor * excess
        order_amount = smoothing_threshold + smoothed_excess

    # Round to nearest integer
    return order_amount
