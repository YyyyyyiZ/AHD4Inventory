# policy_hash: ffe9fbeb1abc341aebbc75bd35c991a2e71049c531c33f9e74b057c8d39d0c87
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1077.28
# best_prompt_performance: 1074.73
# best_rel_error_pct: 0.236707
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_054821.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 482.6120445772857  # OPT_PARAM: {"initial": 482.6120445772857, "min": 300, "max": 700, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 20, "max": 100, "type": "float"}
    demand_forecast = 102.0  # OPT_PARAM: {"initial": 102.0, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    lead_time_demand = demand_forecast * (lead_time + 1)

    # Calculate target inventory level
    target_inventory = lead_time_demand + safety_stock

    # Use the maximum of base_stock and target_inventory
    order_up_to = max(base_stock, target_inventory)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
