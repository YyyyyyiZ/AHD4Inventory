# policy_hash: b4fb3822fb1cc798ffa2da016c4d0a98ec63a3ac362c9c89d4da5701b453bd19
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 958.73
# best_prompt_performance: 958.73
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_022720.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 232.36608648959663  # OPT_PARAM: {"initial": 232.36608648959663, "min": 200, "max": 400, "type": "float"}
    safety_stock = 62.61804206301202  # OPT_PARAM: {"initial": 62.61804206301202, "min": 50, "max": 250, "type": "float"}
    demand_forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 80, "max": 120, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate order-up-to level
    order_up_to = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing only when order is very large
    smoothing_threshold = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 150, "max": 350, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    if order_amount > smoothing_threshold:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * smoothing_threshold

    # Round to nearest integer
    return order_amount
