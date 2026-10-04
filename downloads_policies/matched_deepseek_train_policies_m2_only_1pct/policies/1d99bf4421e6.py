# policy_hash: 1d99bf4421e67c9e68bf6b5a30c190950665017c858e7778869f7f7a39ec6d4e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 695.01
# best_prompt_performance: 695.01
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_024013.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 235.6679485216122  # OPT_PARAM: {"initial": 235.6679485216122, "min": 200, "max": 280, "type": "float"}
    safety_stock = 55.667948521613624  # OPT_PARAM: {"initial": 55.667948521613624, "min": 40, "max": 100, "type": "float"}
    demand_forecast = 102.1  # OPT_PARAM: {"initial": 102.1, "min": 95, "max": 110, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic order-up-to level based on pipeline status
    pipeline_ratio = sum(pipeline_orders) / (demand_forecast * 2) if demand_forecast > 0 else 1.0
    pipeline_adjustment = 10.667948521580387  # OPT_PARAM: {"initial": 10.667948521580387, "min": 0, "max": 30, "type": "float"}

    order_up_to = base_stock + safety_stock + pipeline_adjustment

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply demand-responsive smoothing
    smoothing_threshold = 96.72585596544907  # OPT_PARAM: {"initial": 96.72585596544907, "min": 70, "max": 120, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    if order_amount > smoothing_threshold:
        excess = order_amount - smoothing_threshold
        smoothed_excess = smoothing_factor * excess
        order_amount = smoothing_threshold + smoothed_excess

    # Round to nearest integer
    return order_amount
