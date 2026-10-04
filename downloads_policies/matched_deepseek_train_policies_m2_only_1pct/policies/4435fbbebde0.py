# policy_hash: 4435fbbebde09af7686d7f252ade6cc07b1afd8ceccae451d5bf7efd63403100
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1904.75
# best_prompt_performance: 1904.75
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_010133.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 781.6283812869356  # OPT_PARAM: {"initial": 781.6283812869356, "min": 400, "max": 900, "type": "float"}
    safety_stock = 117.62955646164474  # OPT_PARAM: {"initial": 117.62955646164474, "min": 20, "max": 150, "type": "float"}
    demand_forecast = 117.3265107735175  # OPT_PARAM: {"initial": 117.3265107735175, "min": 80, "max": 120, "type": "float"}
    adjustment_factor = 0.749172029259321  # OPT_PARAM: {"initial": 0.749172029259321, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_weight = 0.9064278770731122  # OPT_PARAM: {"initial": 0.9064278770731122, "min": 0.0, "max": 1.0, "type": "float"}
    smoothing_factor = 0.09357212292688774  # OPT_PARAM: {"initial": 0.09357212292688774, "min": 0.0, "max": 1.0, "type": "float"}

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
