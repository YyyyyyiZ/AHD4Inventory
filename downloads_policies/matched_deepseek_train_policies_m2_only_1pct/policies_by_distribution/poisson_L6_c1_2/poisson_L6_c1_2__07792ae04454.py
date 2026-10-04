# policy_hash: 07792ae04454756feeea4ff559ef2ed55122e83d7e60dc7d8682e25a9859a152
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1194.22
# best_prompt_performance: 1188.23
# best_rel_error_pct: 0.501583
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_051713.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 580.0  # OPT_PARAM: {"initial": 580.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 85.94998834472182  # OPT_PARAM: {"initial": 85.94998834472182, "min": 20, "max": 100, "type": "float"}
    demand_estimate = 119.83981306847582  # OPT_PARAM: {"initial": 119.83981306847582, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothing_factor = 0.8335505252836709  # OPT_PARAM: {"initial": 0.8335505252836709, "min": 0.3, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Cap the order amount based on demand forecast
    max_order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}
    max_order = max_order_multiplier * demand_estimate
    order_amount = min(order_amount, max_order)

    return order_amount
