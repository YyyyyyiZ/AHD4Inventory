# policy_hash: 835719a55c3aff7dcdb18c380e269a515a44e76646f8cc0e4a1c1496c35244fb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 1291.53
# best_prompt_performance: 1291.53
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_192951.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 691.8746582689654  # OPT_PARAM: {"initial": 691.8746582689654, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 97.36101403707507  # OPT_PARAM: {"initial": 97.36101403707507, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Adjust base stock based on expected demand and safety stock
    adjusted_base_stock = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, adjusted_base_stock)

    # Calculate order quantity
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    return order_amount
