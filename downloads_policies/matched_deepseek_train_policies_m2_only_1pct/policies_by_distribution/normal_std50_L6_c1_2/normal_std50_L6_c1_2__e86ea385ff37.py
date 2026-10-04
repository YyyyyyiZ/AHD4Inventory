# policy_hash: e86ea385ff373e82e80d4a2e26d36740d6229f644149b5d1b31197c0658d06ef
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 4201.72
# best_prompt_performance: 4207.3
# best_rel_error_pct: 0.132803
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_231712.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 451.4821364676808  # OPT_PARAM: {"initial": 451.4821364676808, "min": 200, "max": 800, "type": "float"}
    safety_stock = 81.48213646768126  # OPT_PARAM: {"initial": 81.48213646768126, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.8, "type": "float"}
    demand_lookback = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}
    demand_multiplier = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.8, "max": 2.0, "type": "float"}
    lead_time_factor = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using recent pipeline orders
    if len(pipeline_orders) > 0:
        lookback = min(demand_lookback, len(pipeline_orders))
        recent_orders = pipeline_orders[-lookback:]
        estimated_demand = sum(recent_orders) / lookback * demand_multiplier
    else:
        estimated_demand = 0

    # Calculate lead-time adjusted demand
    lead_time_demand = estimated_demand * lead_time_factor

    # Calculate target inventory position
    target_position = base_stock + safety_stock + lead_time_demand

    # Calculate order quantity with smoothing
    order_needed = max(0, target_position - inventory_position)
    order_amount = smoothing_factor * order_needed

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
