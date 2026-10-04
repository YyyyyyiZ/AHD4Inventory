# policy_hash: dc42ae0121c68e763de1e4cae66ced63b79d7a6446b99f02b815a8037a3ee226
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1469.82
# best_prompt_performance: 1469.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_010854.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 924.3911525710809  # OPT_PARAM: {"initial": 924.3911525710809, "min": 700, "max": 1000, "type": "float"}
    safety_stock = 97.20433364846642  # OPT_PARAM: {"initial": 97.20433364846642, "min": 50, "max": 120, "type": "float"}
    demand_forecast = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 90, "max": 110, "type": "float"}
    adjustment_factor = 0.7999999999999999  # OPT_PARAM: {"initial": 0.7999999999999999, "min": 0.7, "max": 1.0, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = expected_lead_time_demand + safety_stock

    # Blend base_stock and target_inventory based on pipeline status
    effective_base = (pipeline_weight * base_stock +
                     (1 - pipeline_weight) * target_inventory)

    # Smooth the order amount calculation
    raw_order = max(0, effective_base - inventory_position)
    smoothed_order = (smoothing_factor * raw_order +
                     (1 - smoothing_factor) * demand_forecast)

    # Apply adjustment factor and round
    order_amount = max(0, adjustment_factor * smoothed_order)

    # Round to nearest integer
    return order_amount
