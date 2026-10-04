# policy_hash: 5a14900d1f750b8c790dfd3fe2414d6650b2c4a7e213b0d975fabc2d474c6427
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 97
# source_prompt_files: 1
# best_target_performance: 6254.2
# best_prompt_performance: 6254.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_223210.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 692.386088573369  # OPT_PARAM: {"initial": 692.386088573369, "min": 400, "max": 900, "type": "float"}
    safety_stock = 103.1506473601249  # OPT_PARAM: {"initial": 103.1506473601249, "min": 20, "max": 150, "type": "float"}
    demand_forecast = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 180, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}
    lead_time_buffer = 1.8  # OPT_PARAM: {"initial": 1.8, "min": 1.0, "max": 1.8, "type": "float"}
    max_order_multiplier = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 3.0, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time with buffer
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_forecast * lead_time * lead_time_buffer

    # Calculate target inventory level
    target_inventory = lead_time_demand + safety_stock

    # Use weighted average of base_stock and target_inventory
    order_up_to = 0.7 * base_stock + 0.3 * target_inventory

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing with dynamic cap based on forecast
    max_order = demand_forecast * max_order_multiplier
    if order_amount > max_order:
        order_amount = max_order + smoothing_factor * (order_amount - max_order)

    # Round to nearest integer for practical ordering
    return order_amount
