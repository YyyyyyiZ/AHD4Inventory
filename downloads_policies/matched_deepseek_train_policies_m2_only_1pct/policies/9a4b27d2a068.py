# policy_hash: 9a4b27d2a06820c4404337b2c30d36ecbb0e62daae08b3743f011cf7b51d6238
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 4102.63
# best_prompt_performance: 4100.96
# best_rel_error_pct: 0.040706
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_231735.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 606.1983124020614  # OPT_PARAM: {"initial": 606.1983124020614, "min": 400, "max": 800, "type": "float"}
    safety_stock = 106.29831240205822  # OPT_PARAM: {"initial": 106.29831240205822, "min": 50, "max": 200, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    lead_time = 6  # OPT_PARAM: {"initial": 6, "min": 1, "max": 10, "type": "int"}
    demand_multiplier = 1.6615219037600695  # OPT_PARAM: {"initial": 1.6615219037600695, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using pipeline orders
    if len(pipeline_orders) > 0:
        # Use more recent pipeline orders for better demand estimation
        lookback = min(3, len(pipeline_orders))
        recent_orders = pipeline_orders[-lookback:]
        estimated_demand = sum(recent_orders) / lookback * demand_multiplier
    else:
        estimated_demand = 0

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock + estimated_demand

    # Calculate order needed to reach target
    order_needed = max(0, target_inventory - inventory_position)

    # Apply smoothing to prevent large order swings
    order_amount = smoothing_factor * order_needed

    # Ensure order is integer and non-negative
    order_amount = int(round(order_amount))

    return order_amount
