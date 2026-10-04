# policy_hash: c830a8f0441f95da7b185a9db4d93d6d975dcd38ee0d31eb7a8c512b8925827a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 695.07
# best_prompt_performance: 695.07
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_024505.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 242.79776525121548  # OPT_PARAM: {"initial": 242.79776525121548, "min": 200, "max": 260, "type": "float"}
    safety_stock = 60.49776525121455  # OPT_PARAM: {"initial": 60.49776525121455, "min": 30, "max": 80, "type": "float"}
    demand_forecast = 102.21186235113386  # OPT_PARAM: {"initial": 102.21186235113386, "min": 95, "max": 110, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Pipeline-aware adjustment
    pipeline_ratio = sum(pipeline_orders) / (demand_forecast * 2) if demand_forecast > 0 else 1.0
    pipeline_adjustment = 2.80185058383308  # OPT_PARAM: {"initial": 2.80185058383308, "min": 0, "max": 25, "type": "float"}

    # Dynamic order-up-to level
    order_up_to = base_stock + safety_stock - pipeline_adjustment * pipeline_ratio

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Aggressive smoothing for large orders
    smoothing_threshold = 96.7283411542725  # OPT_PARAM: {"initial": 96.7283411542725, "min": 60, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    if order_amount > smoothing_threshold:
        excess = order_amount - smoothing_threshold
        smoothed_excess = smoothing_factor * excess
        order_amount = smoothing_threshold + smoothed_excess

    # Round to nearest integer
    return order_amount
