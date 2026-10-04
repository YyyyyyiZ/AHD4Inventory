# policy_hash: 5e1fc2863eb699ae45aa7c06bcfa69dc39e4f3057ef6eda1993b095c5c04b7e1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 1284.35
# best_prompt_performance: 1284.35
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_005456.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 744.6761600276609  # OPT_PARAM: {"initial": 744.6761600276609, "min": 500, "max": 1200, "type": "float"}
    safety_stock = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 300, "type": "float"}
    demand_forecast = 97.30307527719805  # OPT_PARAM: {"initial": 97.30307527719805, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.0011113185592938786  # OPT_PARAM: {"initial": 0.0011113185592938786, "min": 0.0, "max": 0.8, "type": "float"}
    lead_time_multiplier = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 0.8, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand over lead time with multiplier
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_forecast * lead_time * lead_time_multiplier

    # Calculate order-up-to level
    order_up_to = lead_time_demand + safety_stock

    # Use the maximum of base_stock and calculated order-up-to
    final_order_up_to = max(base_stock, order_up_to)

    # Calculate order amount
    order_amount = max(0, final_order_up_to - inventory_position)

    # Apply smoothing only when order amount is positive
    if order_amount > 0 and smoothing_factor > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    return order_amount
