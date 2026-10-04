# policy_hash: 38c88335ca2a9dd1cf74589c19f37666de2bdf2fb7240cb67f28ec28cb8b671c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2245.31
# best_prompt_performance: 2243.82
# best_rel_error_pct: 0.066361
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_090706.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 635.7760707215455  # OPT_PARAM: {"initial": 635.7760707215455, "min": 400, "max": 900, "type": "float"}
    safety_stock = 95.96079235311035  # OPT_PARAM: {"initial": 95.96079235311035, "min": 50, "max": 200, "type": "float"}
    demand_forecast = 103.5858114786513  # OPT_PARAM: {"initial": 103.5858114786513, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.2740219646946496  # OPT_PARAM: {"initial": 1.2740219646946496, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate effective inventory position
    full_pipeline = sum(pipeline_orders)
    effective_pipeline = full_pipeline * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory with lost-sales adjustment
    target_inventory = base_stock + safety_stock * lost_sales_weight

    # Calculate deficit and order target
    deficit = target_inventory - inventory_position
    order_target = max(0, deficit + demand_forecast)

    # Apply adjustment factor
    order_amount = max(0, order_target * adjustment_factor)

    # Round to nearest integer
    return order_amount
